# coding=utf-8
#---------------------------------------------------------------------------
# Copyright 2011 utahta
#---------------------------------------------------------------------------
try:
    # For Python3
    from urllib.request import urlopen
    from urllib.parse import quote_plus
except ImportError:
    # For Python2
    from urllib2 import urlopen
import math
import time
from jsm.util import html_parser
from jsm.brand import BrandData
import re

class SearchParser(object):
    """銘柄検索ページパーサ"""
    SITE_URL = "http://stocks.finance.yahoo.co.jp/stocks/search/?s=%(terms)s&p=%(page)s&ei=UTF-8"
    DATA_FIELD_NUM = 7 # データの要素数
    COLUMN_NUM = 50 # 1ページ辺り最大行数

    def __init__(self):
        self._elms = []
        self._detail = False
        self._max_page = 0
    
    def fetch(self, terms, page=1):
        """銘柄検索結果を取得
        terms: 検索ワード
        page: ページ
        """
        terms = quote_plus(str(terms))
        siteurl = self.SITE_URL % {'terms':terms, 'page':page}
        fp = urlopen(siteurl)
        html = fp.read()
        fp.close()
        soup = html_parser(html)

        elm = soup.find('div', {'class': 'ymuiPagingTop yjSt clearFix'})
        if elm:
            # 全件数
            max_page = self._text(elm)
            if max_page:
                self._max_page = int(math.ceil(int(max_page) / 15.0))
            # データ
            elm = soup.find("div", {'id': 'sr'})
            self._elms = elm.findAll('div', {'class': 'searchresults clearFix'})
            self._detail = False
        else:
            elm = soup.find('div', {'id': 'main'})
            if elm:
                self._elms = [elm]
                self._max_page = 0
                self._detail = True

    def fetch_all(self, terms, page=1):
        """検索結果を全部取得
        """
        elms = []
        self.fetch(terms, page)
        elms.extend(self._elms)
        for page in range(2, self._max_page+1):
            self.fetch(terms, page)
            elms.extend(self._elms)
            time.sleep(0.5)
        self._elms = elms
        
    def get(self):
        result_set = []
        if not self._elms:
            return result_set
        if self._detail:
            elm = self._elms[0]
            if elm.find('div', {'class': 'stockMainTab clearFix'}):
                name = elm.find('h1').get_text()
                code = elm.find('dl', {'class': 'stocksInfo clearFix'}).find('dt').get_text()
                market = elm.find('span', {'class': 'stockMainTabName'}).get_text()
                info = ''
                res = BrandData(code,
                                market,
                                name,
                                info)
                result_set.append(res)
        else:
            for elm in self._elms:
                name = elm.find('span', {'class': 'name'}).get_text()
                code = elm.find('span', {'class': 'code'}).get_text()[1:-1]
                market = elm.find('span', {'class': 'market'}).get_text()[2:]
                info = elm.find('li', {'class': 'yjMSt greyFin'}).get_text()[4:]
                res = BrandData(code,
                                market,
                                name,
                                info)
                result_set.append(res)
        return result_set
    
    def _market(self, soup):
        return soup.text.encode('utf-8')
    
    def _text(self, soup):
        strong = soup.find("strong")
        if strong:
            return strong.text.encode("utf-8")
        else:
            return ""

class Search(object):
    """銘柄検索
    """
    def get(self, terms):
        p = SearchParser()
        p.fetch_all(terms)
        return p.get()
