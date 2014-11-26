import os
import datetime
import requests
import boto

from ... import settings
from .base import BaseCommand, CommandError


def parse_page(url):
    if not settings.API_KEY:
        raise ValueError('need to set API_KEY (environment variable PUPA_API_KEY)')
    data = requests.get(url + '&apikey=' + settings.API_KEY).json()
    for person in data['results']:
        id = person['id']
        pjson = requests.get('https://api.opencivicdata.org/{}/?apikey={}'.format(id,
                                                                                  settings.API_KEY))
        dirname = os.path.dirname(id)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        with open(id, 'w') as f:
            f.write(pjson.text)
    page = data['meta']['page'] + 1
    return page if page <= data['meta']['max_page'] else None


def dump_pages(endpoint):
    page = 1
    while page:
        page = parse_page('https://api.opencivicdata.org/{}/?fields=id&page={}'.format(
            endpoint,
            page
        ))


def dump_jurisdictions():
    dump_pages('jurisdictions')


def dump_people():
    dump_pages('people')


def dump_organizations():
    dump_pages('organizations')


def dump_bills():
    dump_pages('bills')


def upload(filename, bucket, s3_path):
    if not settings.AWS_KEY or not settings.AWS_SECRET:
        raise ValueError('need to set AWS_KEY and AWS_SECRET')
    s3 = boto.connect_s3(settings.AWS_KEY, settings.AWS_SECRET)
    bucket = s3.create_bucket(bucket)
    k = boto.s3.key.Key(bucket)
    k.key = s3_path
    k.set_contents_from_filename(filename)
    k.set_acl('public-read')


class Command(BaseCommand):
    name = 'dump'
    help = 'create a dump of pupa data and upload to S3'

    def add_args(self):
        pass
        #self.add_argument('module', type=str, help='name of the new scraper module')

    def handle(self, args, other):
        bucket = 'allthe.opencivicdata.org'
        fname = 'ocd-allpeople.tar.gz'
        dump_jurisdictions()
        dump_bills()
        dump_people()
        dump_organizations()
        os.system('tar cf {} ocd-person/'.format(fname))
        upload(fname, bucket, fname)
        upload(fname, bucket, datetime.date.today().strftime('%Y%m%d-') + fname)
