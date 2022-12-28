import re
import aiohttp
import LOGGER
import asyncio
import math
from bs4 import BeautifulSoup
import LOGGER
from re import findall as re_findall, search as re_search

async def direct_link_generator(link: str):
    """ direct links generator """
    if 'youtube.com' in link or 'youtu.be' in link:
        LOGGER.error("ERROR: Use ytdl cmds for Youtube links")
        raise DirectDownloadLinkException("ERROR: Use ytdl cmds for Youtube links")
    elif 'yadi.sk' in link or 'disk.yandex.com' in link:
        return await yandex_disk(link)
    elif 'mediafire.com' in link:
        return await mediafire(link)
    elif 'zippyshare.com' in (link):
        return zippy_share(link)

async def yandex_disk(url: str) -> str:
    """ Yandex.Disk direct link generator
    Based on https://github.com/wldhx/yadisk-direct """
    try:
        link = re.findall(r'\b(https?://(yadi.sk|disk.yandex.com)\S+)', url)[0][0]
    except IndexError:
        LOGGER.warning("No Yandex.Disk links found")
        return "No Yandex.Disk links found\n"
    api = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api.format(link)) as resp:
                return (await resp.json())['href']
    except KeyError:
        LOGGER.error("ERROR: File not found/Download limit reached")
        raise DirectDownloadLinkException("ERROR: File not found/Download limit reached")

async def mediafire(url: str) -> str:
    """ MediaFire direct link generator """
    try:
        link = re.findall(r'\bhttps?://.*mediafire\.com\S+', url)[0]
    except IndexError:
        LOGGER.warning("No MediaFire links found")
        raise DirectDownloadLinkException("No MediaFire links found")
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as resp:
            page = BeautifulSoup(await resp.text(), 'lxml')
    info = page.find('a', {'aria-label': 'Download file'})
    return info.get('href')

async def zippy_share(url: str) -> str:
    base_url = re_search('http.+.zippyshare.com', url).group()
    response = rget(url)
    pages = BeautifulSoup(response.text, "html.parser")
    js_script = pages.find("div", style="margin-left: 24px; margin-top: 20px; text-align: center; width: 303px; height: 105px;")
    if js_script is None:
        js_script = pages.find("div", style="margin-left: -22px; margin-top: -5px; text-align: center;width: 303px;")
    js_script = str(js_script)

    try:
        var_a = re_findall(r"var.a.=.(\d+)", js_script)[0]
        mtk = int(math_pow(int(var_a),3) + 3)
        uri1 = re_findall(r"\.href.=.\"/(.*?)/\"", js_script)[0]
        uri2 = re_findall(r"\+\"/(.*?)\"", js_script)[0]
    except:
        try:
            a, b = re_findall(r"var.[ab].=.(\d+)", js_script)
            mtk = eval(f"{math_floor(int(a)/3) + int(a) % int(b)}")
            uri1 = re_findall(r"\.href.=.\"/(.*?)/\"", js_script)[0]
            uri2 = re_findall(r"\)\+\"/(.*?)\"", js_script)[0]
        except:
            try:
                mtk = eval(re_findall(r"\+\((.*?).\+", js_script)[0] + "+ 11")
                uri1 = re_findall(r"\.href.=.\"/(.*?)/\"", js_script)[0]
                uri2 = re_findall(r"\)\+\"/(.*?)\"", js_script)[0]
            except:
                try:
                    mtk = eval(re_findall(r"\+.\((.*?)\).\+", js_script)[0])
                    uri1 = re_findall(r"\.href.=.\"/(.*?)/\"", js_script)[0]
                    uri2 = re_findall(r"\+.\"/(.*?)\"", js_script)[0]
                except Exception as err:
                    LOGGER.error(err)
                    raise DirectDownloadLinkException("ERROR: Tidak dapat mengambil direct link")
    dl_url = f"{base_url}/{uri1}/{int(mtk)}/{uri2}"
    return dl_url


