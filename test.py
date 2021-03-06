from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import json
import requests
import threading

listenAddr = "128.199.82.190"
listenPort = 7655
pagureRepo = "docs-test"
pagureToken = "token L984SSW08QBFVEHF5IXVVWT9HNQJTX8HNSUM2XL6ECV7KUFKD7HHCYROIG0ZGGEJ"
pagureHeader = {"Authorization": pagureToken}
# TODO: this is a test propose token
githubToken = "token "
githubHeader = {"Authorization": githubToken}

# TODO: how to handle merge conflict

r = requests.get("https://pagure.io/api/0/" + pagureRepo + "/issues", headers=pagureHeader)
init_file = r.text
init_json = json.loads(init_file)
last_issue_list = init_json['issues']
githubUsername = "yangl1996"
githubRepo = "doc-test"


def search_for_fixed():
    time.sleep(1)
    global last_issue_list
    q = requests.get("https://pagure.io/api/0/" + pagureRepo + "/issues", headers=pagureHeader)
    new_file = q.text
    new_json = json.loads(new_file)
    new_issue_list = new_json['issues']
    difference = [item for item in last_issue_list if item not in new_issue_list]
    while not difference:
        time.sleep(1)  # wait for 1 second
        q = requests.get("https://pagure.io/api/0/" + pagureRepo + "/issues", headers=pagureHeader)
        new_file = q.text
        new_json = json.loads(new_file)
        new_issue_list = new_json['issues']
        difference = [item for item in last_issue_list if item not in new_issue_list]
    last_issue_list = new_issue_list
    deleted_title = difference[0]['title']
    print("Fixed: ", deleted_title)
    # TODO: need sync to github
    PR_id = int(deleted_title[1:deleted_title.find(' ')])
    r = requests.get("https://api.github.com/repos/{}/{}/pulls/{}".format(githubUsername, githubRepo, PR_id),
                     headers=githubHeader)
    return_data = json.loads(r.text)
    PR_sha = return_data['head']['sha']
    merge_payload = json.dumps({"commit_message": "Merge pull request" + str(PR_id), "sha": PR_sha})
    r = requests.put('https://api.github.com/repos/{}/{}/pulls/{}/merge'.format(githubUsername, githubRepo, PR_id),
                     headers=githubHeader, data=merge_payload)
    print(r.text)


def search_for_added():
    time.sleep(1)
    global last_issue_list
    q = requests.get("https://pagure.io/api/0/" + pagureRepo + "/issues", headers=pagureHeader)
    new_file = q.text
    new_json = json.loads(new_file)
    new_issue_list = new_json['issues']
    difference = [item for item in new_issue_list if item not in last_issue_list]
    while not difference:
        time.sleep(1)  # wait for 1 second
        q = requests.get("https://pagure.io/api/0/" + pagureRepo + "/issues", headers=pagureHeader)
        new_file = q.text
        new_json = json.loads(new_file)
        new_issue_list = new_json['issues']
        difference = [item for item in new_issue_list if item not in last_issue_list]
    last_issue_list = new_issue_list
    added_title = difference[0]['title']
    print("Added: ", added_title)


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        global last_issue_list
        content_len = int(self.headers['content-length'])
        post_body = self.rfile.read(content_len).decode()
        self.send_response(200)
        self.end_headers()
        if self.headers['X-Pagure-Topic'] == "issue.edit":
            th = threading.Thread(target=search_for_fixed)
            th.start()
        if self.headers['X-Pagure-Topic'] == "issue.new":
            th = threading.Thread(target=search_for_added)
            th.start()


myServer = HTTPServer((listenAddr, listenPort), MyServer)
print("Test Server")
print(time.asctime(), "Server Starts - %s:%s" % (listenAddr, listenPort))

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()
print(time.asctime(), "Server Stops - %s:%s" % (listenAddr, listenPort))