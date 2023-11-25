import requests
import json
import os
import shutil
import datetime
from git import Repo
from pytz import timezone

# 사용자로부터 검색어 입력 받기
search_query = 'org:apache  language:Java' #input("GitHub에서 어떤 주제로 검색하시겠습니까? ")

# 사용자로부터 폴더 위치 입력 받기
folder_path = 'out' #input("JSON 파일을 저장할 폴더의 경로를 입력하세요: ")

# 검색어와 폴더 위치를 기반으로 JSON 파일 경로 생성
now = datetime.datetime.now()
timestamp = now.strftime("%Y%m%d%H%M%S")
json_filename = f"github_ranking_{search_query}_{timestamp}.json"
json_filepath = os.path.join(folder_path, json_filename)

# GitHub API 엔드포인트에 검색어 추가
url = f"https://api.github.com/search/repositories?q={search_query}+stars:%3E1&sort=stars&order=desc"

# GitHub API에 요청을 보내서 데이터 가져오기
response = requests.get(url)
data = response.json()

# JSON 파일에 저장할 데이터 추출
repositories = data["items"]
ranked_repositories = []

for i, repo in enumerate(repositories):
    ranked_repositories.append({
        "Rank": i + 1,
        "Name": repo["name"],
        "Owner": repo["owner"]["login"],
        "Stars": repo["stargazers_count"],
        "URL": repo["html_url"]
    })


keywords = ['bug', 'fix']

# JSON 파일에서 GitHub 저장소 URL 가져오기
repo_urls = [repo["URL"] for repo in ranked_repositories]

# JSON 파일에 저장할 데이터 추출
commit_data = []

start_date = timezone('UTC').localize(datetime.datetime(2020, 1, 1))
end_date = timezone('UTC').localize(datetime.datetime(2022, 11, 6))

java_file_extensions = '.java'

for repo_url in repo_urls:
    # GitHub 저장소를 클론하여 커밋 메시지 분석
    repo_name = repo_url.split("/")[-1]
    repo_path = os.path.join(folder_path, repo_name)

    owner_repo_name = repo_url.split("/")[-2] + '/' + repo_name

    if not os.path.exists(repo_path):
        Repo.clone_from(repo_url, repo_path)

    repo = Repo(repo_path)

    
    for commit in repo.iter_commits():
        commit_date = commit.committed_datetime
        if start_date <= commit_date <= end_date:
            commit_message = commit.message
            if keywords[0] in commit_message and keywords[1] in commit_message:
                commit_data.append({
                    "fix_commit_hash": commit.hexsha,
                    "repo_name": owner_repo_name,
                    "repo_url" : repo_url
                })
            # for keyword in keywords:
            #     if keyword in commit_message:
            #         commit_data.append({
            #             "fix_commit_hash": commit.hexsha,
            #             "repo_name": owner_repo_name,
            #             "repo_url" : repo_url
            #         })

    # 클론된 저장소 디렉토리 삭제
    shutil.rmtree(repo_path)

# 결과를 JSON 파일로 저장
result_json_filename = f"commits_with_keywords_{timestamp}.json"
result_json_filepath = os.path.join(folder_path, result_json_filename)

with open(result_json_filepath, 'w', newline='') as result_json_file:
    json.dump(commit_data, result_json_file, indent=2)

print(f"커밋 메시지에서 키워드를 포함하는 모든 커밋이 '{result_json_filepath}' 파일에 저장되었습니다.")

