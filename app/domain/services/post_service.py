import requests
from bs4 import BeautifulSoup


class PostService:
    @staticmethod
    def get_opengraph_data(url):
        try:
            response = requests.get(url)
            encoding = response.apparent_encoding  # レスポンスからエンコーディングを取得
            response.encoding = encoding  # レスポンスのエンコーディングを設定
            soup = BeautifulSoup(response.text, "html.parser")
            og_title = soup.find("meta", property="og:title")
            og_description = soup.find("meta", property="og:description")
            og_image = soup.find("meta", property="og:image")
            return {
                "title": og_title["content"] if og_title else None,
                "description": og_description["content"] if og_description else None,
                "image": og_image["content"] if og_image else None,
            }
        except Exception as e:
            print(f"Error fetching OpenGraph data: {e}")
            return None

    @staticmethod
    def generate_opengraph_preview(url):
        opengraph_data = PostService.get_opengraph_data(url)
        if opengraph_data:
            preview_html = f"""
                <div class="og box">
                    <article class="media">
                        <figure class="media-left">
                            <p class="image is-128x128">
                                <img src="{opengraph_data['image']}" alt="Preview image" style="border-radius: 8px;">
                            </p>
                        </figure>
                        <div class="media-content">
                            <div class="content">
                                <p>
                                    <strong>{opengraph_data['title']}</strong> <br>
                                    {opengraph_data['description']}
                                </p>
                            </div>
                            <nav class="level is-mobile">
                                <div class="level-left">
                                    <a href="{url}" target="_blank" class="button is-link">Read more...</a>
                                </div>
                            </nav>
                        </div>
                    </article>
                </div>
            """
            return preview_html
        else:
            return None
