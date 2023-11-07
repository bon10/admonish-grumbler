import re

import markdown


class MessageConverter:
    @staticmethod
    def convert_message(text):
        # Markdown変換後のリンクが二重に変換されないように、既に <a> タグで囲まれていないURLのみを変換
        # href属性の値でないURLにマッチする
        url_pattern = r'(?<!href=")http[s]?://[^\s<>"\'()]+'
        html_link_pattern = r'<a href="\g<0>" target="_blank">\g<0></a>'
        converted_text = re.sub(url_pattern, html_link_pattern, text)

        # 改行を<br/>に変換
        converted_text = converted_text.replace('\n', '<br/>')
        return converted_text

    def convert_markdown(text):
        converted_text = markdown.markdown(text)
        return converted_text
