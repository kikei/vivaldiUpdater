import requests
import os
from pyquery import PyQuery
from urllib.parse import urlparse, urljoin
import posixpath
import zipfile

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.98 Safari/537.36 Vivaldi/1.6.689.46'
VIVALDI_COM_URL = 'https://vivaldi.com/download/'
LIBFFMPEG_URL = 'https://github.com/iteufel/nwjs-ffmpeg-prebuilt/releases/latest'
LIBFFMPEG = '/opt/vivaldi/lib/libffmpeg.so'

def http_get(url):
  headers = {
    'User-Agent': USER_AGENT
  }
  res = requests.get(url)
  return res

def make_filename(url, dest_dir):
  r = urlparse(url)
  name = posixpath.basename(r.path)
  filename = os.path.join(dest_dir, name)
  return filename

def download_to(url, dest_file):
  r = urlparse(url)
  name = posixpath.basename(r.path)
  print('Downloading {}...'.format(name))
  res = http_get(url)
  with open(dest_file, 'wb') as wb:
    wb.write(res.content)
    wb.close()
  print('done.')

def download_to_dir(url, dest_dir):
  out_file = make_filename(url, dest_dir)
  download_to(url, out_file)

class VivaldiClawler(object):
  def get_vivaldi_com(self):
    res = http_get(VIVALDI_COM_URL)
    return PyQuery(res.text)

  def get_download_links(self):
    dom = self.get_vivaldi_com()
    anchors = dom('a')
    for a in anchors.items():
      href = a.attr['href']
      if href.find('downloads') > 0:
        yield href
  
  def get_download_links_for(self, parts):
    links = self.get_download_links()
    for link in links:
      matched = list(filter(lambda p:link.find(p) > -1, parts))
      if len(matched) != len(parts):
        continue
      yield link
  
  def get_download_link_for(self, parts):
    links = self.get_download_links_for(parts)
    link = next(links)
    return link


class LibFFmpegClawler(object):
  def __init__(self, url):
    self.url = url
  
  def get_libffmpeg_releases(self):
    res = http_get(self.url)
    return PyQuery(res.text)

  def get_download_links(self):
    dom = self.get_libffmpeg_releases()
    anchors = dom('a')
    for a in anchors.items():
      href = a.attr['href']
      if href.find('download') > 0:
        yield href
  
  def get_download_links_for(self, parts):
    links = self.get_download_links()
    for link in links:
      matched = list(filter(lambda p:link.find(p) > -1, parts))
      if len(matched) != len(parts):
        continue
      yield link
  
  def get_download_link_for(self, parts):
    links = self.get_download_links_for(parts)
    link = next(links)
    if link is not None:
      link = urljoin(self.url, link)
    return link


def download_vivaldi(dest_dir):
  clawler = VivaldiClawler()
  url = clawler.get_download_link_for(['x86_64', 'rpm'])
  filename = make_filename(url, dest_dir)
  if os.path.isfile(filename):
    return None
  download_to(url, filename)
  return filename

def download_libffmpeg(dest_dir):
  clawler = LibFFmpegClawler(LIBFFMPEG_URL)
  url = clawler.get_download_link_for(['linux', 'x64'])
  filename = make_filename(url, dest_dir)
  if os.path.isfile(filename):
    return None
  download_to(url, filename)
  zipFile = zipfile.ZipFile(filename)
  zipFile.extract('libffmpeg.so', dest_dir)
  zipFile.close()
  filename = os.path.join(dest_dir, 'libffmpeg.so')
  return filename

def main():
  PWD = os.path.dirname((os.path.abspath(__file__)))
  download_dir = os.path.join(PWD, '..', 'data')
  os.makedirs(download_dir, mode=755, exist_ok=True)
  vivaldi_file = download_vivaldi(download_dir)
  libffmpeg_file = download_libffmpeg(download_dir)
  
  commands = []
  
  if vivaldi_file is not None:
    commands.append('dnf install {src}'.format(src=vivaldi_file))
  
  if libffmpeg_file is not None:
    commands.append('install {src} {dest}'.format(src=libffmpeg_file, dest=LIBFFMPEG))
  
  if len(commands) == 0:
    print('Not updated.')
  else:
    print('Update found, run following command:')
    script = '''
#!/bin/sh

sudo -- sh -c '{command}'
'''.strip()
    script = script.format(command='; '.join(commands))
    print(script)


main()
