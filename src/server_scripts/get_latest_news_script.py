from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

def getLatestCyberSecurityNews(k=5):
    def TheHackerNewsSearch():
        HTMLData = requests.get("https://thehackernews.com/")
        soup = BeautifulSoup(HTMLData.text, 'html.parser')
        elements = soup.find_all(class_="body-post clear")
        news_list = []
        for body_post in elements:
            story_link = body_post.select_one('.story-link')
            href = story_link.get('href')
            data = requests.get(href)
            info = BeautifulSoup(data.text, 'html.parser')
            header = info.select_one('.story-title')
            content = info.find_all(['p','h2'])
            content = content[:-8]
            content = [element for element in content if not (element.name == 'p' and element.find('em'))]
            content = "\n".join(["**" + i.text + "**" if i.name == 'h2' else i.text for i in content])
            date = info.select_one('.author')
            date = datetime.strptime(date.text, "%b %d, %Y").date()
            news = {
                'Name': header.text,
                'Content': content,
                'Date': date,
                'Ref': href,
            }
            news_list.append(news)
        return news_list

    def DarkReadingSearch():
        def find_date_indices(text_list):
          for index, text in enumerate(text_list):
              try:
                  datetime.strptime(text, "%B %d, %Y")
                  return index
              except ValueError:
                  continue
          return None
        def find_space_indices(text_list):
          for index, text in enumerate(text_list):
              if text == "**About the Author**" or text == "Read more about:":
                  return index
          return None
        HTMLData = requests.get("https://www.darkreading.com/")
        soup = BeautifulSoup(HTMLData.text, 'html.parser')
        elements = soup.find_all(class_='ContentPreview LatestFeatured-ContentItem LatestFeatured-ContentItem_left')
        news_list = []
        for body_post in elements:
            story_link = body_post.select_one('.ListPreview-Title')
            href = "https://www.darkreading.com"+story_link.get('href')
            data = requests.get(href)
            info = BeautifulSoup(data.text, 'html.parser')
            header = info.select_one('.ArticleBase-LargeTitle')
            content = info.find_all(['p', 'h2'])
            content = ["**" + i.text + "**" if i.name == 'h2' else i.text for i in content]
            date_index = find_date_indices(content)
            space_index = find_space_indices(content)
            date = datetime.strptime(content[date_index], "%B %d, %Y").date()
            content = content[date_index+1:space_index]
            news = {
                'Name': header.text,
                'Content': "\n".join(content),
                'Date': date,
                'Ref': href,
            }
            news_list.append(news)
        return news_list

    def SecurityAffairsSearch():
        def find_split_indices(text_list):
            for index, text in enumerate(text_list):
                if text.strip().replace('\u00A0', ' ') == "Follow me on Twitter: @securityaffairs and Facebook and Mastodon":
                    return index
            return None
        HTMLData = requests.get("https://securityaffairs.com/category/cyber-crime")
        soup = BeautifulSoup(HTMLData.text, 'html.parser')
        elements = soup.find_all(class_='news-card news-card-category mb-3 mb-lg-5')
        news_list = []
        for body_post in elements:
            story_link = body_post.select_one('a')
            href = story_link.get('href')
            data = requests.get(href)
            info = BeautifulSoup(data.text, 'html.parser')
            content = info.find('div', class_="article-details-block wow fadeInUp")
            content = content.find_all(['p', 'h2'])
            content = ["**" + i.text + "**" if i.name == 'h2' else i.text for i in content]
            header = content[0]
            split_index = find_split_indices(content)
            content = content[1:split_index]
            date = info.select(".post-time.mb-3")
            date = date[0]
            date = date.select('span')
            date = date[1].text
            date = datetime.strptime(date, " %B %d, %Y").date()
            news = {
                'Name': header,
                'Content': "\n".join(content),
                'Date': date,
                'Ref': href,
            }
            news_list.append(news)
        return news_list

    news_list = TheHackerNewsSearch() + DarkReadingSearch() + SecurityAffairsSearch()
    sorted_news_list = sorted(news_list, key=lambda news: news['Date'], reverse=True)
    sorted_news_list = sorted_news_list[:k]

    return sorted_news_list

def getLatestNews():
    x = getLatestCyberSecurityNews(k=1)
    messages = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an AI assistant specialized in analyzing and summarizing cybersecurity news and discussions from Hacker News. Your goal is to provide concise yet comprehensive summaries that help cybersecurity professionals quickly understand key threats, vulnerabilities, tools manual and industry trends."),
        ("human", 
"""Please analyze the following Hacker News content and generate a structured JSON summary with the following elements:

- **title**: 
  - **original**: The original title of the Hacker News post, if available.
  - **type**: Specify 'Original HN Title' if the title is present, otherwise 'No Title Available'.
  - **generated_topic**: If no original title exists, provide a concise phrase summarizing the main topic.

- **type**: Classify the content as one of the following: 'News Article', 'Discussion Thread', or 'Technical Post'.

- **overview**: Summarize the core topic and key points in 2-3 sentences, focusing on clarity and relevance.

- **threat_analysis**: 
  - **threat_level**: Categorize the threat as 'critical', 'high', 'medium', 'low', or 'informational'.
  - **affected_systems**: List any systems or technologies impacted.
  - **potential_impact**: Briefly describe the possible consequences.

- **key_points**: 
  - **category**: Select from 'Vulnerability', 'Exploit', 'Mitigation', 'Industry Trend', or 'Tool'.
  - **description**: Provide a brief description of the key point.
  - **relevance**: Explain the importance of this point for cybersecurity professionals.
  - Add additional key points as necessary, sorted by relevance.

- **technical_details**: 
  - **cve_ids**: List any mentioned CVE IDs.
  - **iocs**: Include any Indicators of Compromise if mentioned.
  - **affected_versions**: Specify the affected software or system versions, if noted.

- **actionable_insights**: 
  - **priority**: Rank the action as 'high', 'medium', or 'low'.
  - **action**: Suggest a specific action for cybersecurity teams to take.
  - **rationale**: Provide a brief explanation of why this action is important.
  - Include additional insights as needed, prioritized accordingly.

- **related_topics**: List any related cybersecurity topics or keywords relevant to the content.

Guidelines:
1. If an original title exists, use it in the "original" field and set "type" to "Original HN Title". If not, set "original" to null, "type" to "No Title Available", and create a factual "generated_topic".
2. Ensure the "generated_topic" is a precise and neutral summary, not a creative or speculative title.
3. The "overview" should capture the essence of the cybersecurity issue or topic concisely.
4. "threat_analysis" should accurately assess the severity and potential impact of any discussed threats.
5. Focus "key_points" on critical information most relevant to cybersecurity professionals.
6. "technical_details" should be accurate and contextually relevant.
7. "actionable_insights" should be practical, prioritized steps for cybersecurity teams, aiding in quick decision-making.
8. The summary should highlight the most crucial information for efficient decision-making in a cybersecurity context.

Hacker News content to analyze:
{text}
""")
])
    parser = StrOutputParser()
    llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
    chain = {"text": RunnablePassthrough()} | messages | llm | parser
    return chain.invoke(x[0]) # Change the number of content here

current_datetime = datetime.now()
temp_date = current_datetime.strftime("%d-%m-%Y")
fetched_news = getLatestNews()
def getLastestWithDate(last_update):
    global temp_date
    global fetched_news
    if temp_date != last_update:
        temp_date = last_update
        fetched_news = getLatestNews()
    return temp_date, fetched_news