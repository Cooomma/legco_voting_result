import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from fire import Fire


class COLOR:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CommandLine:

    def __init__(self) -> None:
        self.page_url = 'https://www.elections.gov.hk/legco2018kwby/chi/rs_gc_LC2.html'

    @staticmethod
    def _parse_datetime(date_str: str, time_str: str) -> str:
        return datetime.strptime('{} {}'.format(date_str, time_str), "%d/%m/%Y (%H:%M:%S)")

    def get_vote(self):
        URL = 'https://www.elections.gov.hk/legco2018kwby/js/LC2votecount.js'
        data = requests.get(URL).text.split('var')[1:]
        votes = {}
        for line in data:
            line = line.replace(' ', '').replace('\r\n', '').replace(';', '').replace('\"', '').split('=')
            if line:
                votes.update({line[0]: line[1]})
        return dict(
            station_count=int(votes['stationCnt']),
            station_completed=int(votes['stationCompleted']),
            vote_count=list(map(int, votes['voteCnt'].replace('[', '').replace(']', '').split(','))),
            updated_at=self._parse_datetime(votes['updateDate'], votes['updateTime']).strftime("%Y/%m/%d %H:%M:%S")
        )

    def get_candidate(self):
        response = requests.get(self.page_url).text
        bs = BeautifulSoup(response, features='lxml')
        datas = bs.select('td[class*=candidate]')
        candidates = {}
        for number, name, _ in [datas[i:i+3] for i in range(0, len(datas), 3)]:
            candidate_number = int(number.text)
            candidates.update({int(candidate_number): dict(
                name=name.text.encode().decode('ascii', 'replace').replace(u'\ufffd', ''),
                votes=0
            )})
        return candidates

    def outcome(self):
        candidates = self.get_candidate()
        vote_info = self.get_vote()
        votes = vote_info['vote_count']
        dominator = votes.index(max(votes))
        for idx, vote in enumerate(votes):
            if idx < len(votes) - 1:
                candidates[idx+1]['votes'] = vote
            else:
                valid_vote = vote

        del vote_info['vote_count']
        outcome = dict(
            request_ts=int(datetime.utcnow().timestamp()),
            candidates=candidates,
            valid_vote=valid_vote,
            progress=float(vote_info['station_completed'])/float(vote_info['station_count']),
            dominator=candidates[dominator]['name'])
        outcome.update(vote_info)
        return outcome

    def real_time_update(self):
        from pprint import pprint
        import time
        while True:
            pprint(self.outcome())
            print('\n')
            time.sleep(30)


if __name__ == "__main__":
    Fire(CommandLine)
