import streamlit as st

from bs4 import BeautifulSoup
import requests
import json
import re
import regex

def get_soup(url):
    response = requests.get(url)
    response.encoding = response.apparent_encoding
    html = response.text
    return BeautifulSoup(html, 'html.parser')


class WikiParser:
    def __init__(self, url):
        self.url = url
        self.title = url.split("/")[-1]
        self.album_template_params = \
        ['Name',
         'Type',
         'Artist',
         'Released',
         'Recorded',
         'Genre',
         'Length',
         'Label',
         'Producer',
         'Reviews',
         'Chart position',
         'Certification',
         'Last album',
         'This album',
         'Next album',
         'EAN',
         'Tracklist']
        self.tracklist_text = None
        self.references_text = None
        self.album_title = None
        self.artist = None
        self.ja_link = None
        
    def parse_album_template(self):
        section = 0
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={self.title}&prop=wikitext&section={section}&format=json"
        soup = get_soup(url)
        text = json.loads(soup.text)["parse"]["wikitext"]["*"]        
                
        matches = regex.findall("(?<rec>{{(?:[^\{\}]+|(?&rec))*}})", text)
        for match in matches:
            if match.startswith("{{Infobox album"):
                album_infobox_text = match

        def callback(match):
            indent = match.group(1) if match.group(1) is not None else ""
            return f"{indent}| {match.group(2).strip().capitalize()} = "
    
        album_infobox_text = re.sub("^([\s]*)\|(.*?)=", callback, album_infobox_text, flags=re.MULTILINE)
        album_infobox_text = re.sub("\| Next_title", "| Next album", album_infobox_text)
        album_infobox_text = re.sub("\| Prev_title", "| Last album", album_infobox_text)
        album_infobox_text = re.sub("\| Name (.*)", "| Name \\1 \n| This album \\1", album_infobox_text)
        
        self.album_title = album_infobox_text.split("| Name = ")[-1].split("\n")[0].strip()
        self.artist = album_infobox_text.split("| Artist = ")[1].split("\n")[0].strip()
        self.album_text = album_infobox_text
        
    def parse_tracklist(self):
        section_index = self._parse_section_index_by_title("Track listing")
        if section_index is None: return None
        
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={self.title}&prop=wikitext&section={section_index}&format=json"
        soup = get_soup(url)
        text = json.loads(soup.text)["parse"]["wikitext"]["*"]

        text = re.sub("=[\s]*Track listing[\s]*=", "= ?????? =", text)
        self.tracklist_text = text 
        
    def parse_references(self):
        section_index = self._parse_section_index_by_title("References")
        if section_index is None: return None
        
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={self.title}&prop=wikitext&section={section_index}&format=json"
        soup = get_soup(url)
        text = json.loads(soup.text)["parse"]["wikitext"]["*"]

        text = re.sub("=[\s]*References[\s]*=", "= ???????????? =", text)
        self.references_text = text        
        
    def parse_ja_link(self):
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={self.title}&prop=langlinks&format=json"
        soup = get_soup(url)
        langlinks = json.loads(soup.text)["parse"]["langlinks"]
        for langlink in langlinks:
            if langlink["lang"] == "ja":
                self.ja_link = langlink["url"]

    def _parse_section_index_by_title(self, title):
        url = f"https://en.wikipedia.org/w/api.php?action=parse&page={self.title}&prop=sections&format=json"
        soup = get_soup(url)
        sections = json.loads(soup.text)["parse"]["sections"]        
        for section in sections:
            if section["line"] == title: return section["index"]                               

 
header_text = \
"""
# Wikipedia Album (En ??? Ja)

1. ??????????????????URL????????????????????????
1. ??????????????????????????????????????????????????????????????????
"""
st.markdown(header_text)            
url = st.text_input("Input URL (English page)", "https://en.wikipedia.org/wiki/Let_It_Be_(Beatles_album)")

if st.button("??????"):
    with st.spinner():
        st.markdown(f"[????????????]({url})", unsafe_allow_html=True)
        wiki = WikiParser(url)
        wiki.parse_ja_link()
        if wiki.ja_link is None:
            ja_link_text = "???????????????????????????????????????"
            ja_link = f"https://ja.wikipedia.org/wiki/{wiki.title}"
        else:
            ja_link_text = "??????????????????"
            ja_link = wiki.ja_link
        st.markdown(f"[{ja_link_text}]({ja_link})")
        
        wiki.parse_album_template()
        wiki.parse_tracklist()
        wiki.parse_references()

    text = \
    f"""
???'''{wiki.album_title}'''??????{wiki.artist}??????????????????

{wiki.album_text}

{wiki.tracklist_text}

{wiki.references_text}
    """
    st.code(text)

