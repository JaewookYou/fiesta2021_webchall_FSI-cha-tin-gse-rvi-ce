# fiest2021_webchall

- 출제자 : 보안평가2팀 주임 유재욱

- 출제분야 : 웹해킹

- Flag : 미정(추후 마음대로 지정 가능)

  

## 문제 컨셉

- 전체 문제 서비스의 큰 틀은 **채팅 서비스**

- 여러 금융 기관의 취약점 분석 평가시 마주쳤던 채팅상담 서비스의 환경과 비슷한 맥락으로 구성

- 보통 외부의 채팅상담 서비스를 가져와 Integration을 하여 구현하는것이 보통

- 때문에 별도의 채팅상담 서비스 서버를 두고, 웹서버는 클라이언트와 채팅상담 서비스 사이를 중계해주는 역할을 수행

- 이러한 환경에서, 중계 서비스에 SSRF(Server Side Request Forgery) 취약점이 존재한다면 발생하는 위협이 핵심 문제 해결 포인트

  

## 문제 환경

- 서버 언어는 python flask

- flask_socketio(외부망 웹서버) / socketserver(내부망 채팅api 서버) / mysql(내부망 채팅 데이터베이스 서버)

- Client와 웹서버는 socketio를 통해 통신하고, 클라이언트로부터 전달받은 데이터를 파싱하여 내부망 채팅 api 서버로 전송

- 내부망 채팅 api 서버는 웹서버로부터 전달받은 데이터를 토대로 채팅 Database에 질의하여 그 결과를 다시 웹서버로 반환

- 웹서버는 반환받은 채팅 관련 데이터를 클라이언트로 전달

  

## 대략적인 풀이 방법

* 웹서버에서 SSRF를 트리거하려면 잘못 처리된 try / except 구문을 이용하여야함

* 또한 SSRF의 결과를 클라이언트에 정상적으로 전달하기 위해 "나에게 보내기" 기능에선 session에 물린 `loginid` 값을 토대로 socketio의 room을 지정하는 것을 이용하여야 함
* SSRF를 하기 위해 호스트와 포트를 지정할 때 숨겨진 파라미터를 이용
  * 클라이언트에서 해당 파라미터를 보내지 않으면 서버에서 설정된 기본값으로 채팅api 서버와 통신
  * 클라이언트에서 host와 port를 지정하면 그 서버로 통신
  * 해당 조건을 알아내기 위해선 외부망 웹서버의 File Leak이 필수적임
    * 아직 외부망 웹서버의 File Leak을 어떻게 시킬지는 미정
    * ssti / curl lfi 등 고려중

* 해당 파라미터를 통해 host와 port를 지정할 수 있는데, 이를 내부망의 mysql 서버 주소와 포트(3306)로 지정

* 내부망 웹서버(채팅api서버)의 File Leak을 통해 DB Connection 정보를 탈취

  * 아직 내부망 웹서버의 File Leak을 어떻게 시킬지는 미정
  * 대략 사용자의 프로필사진을 가져오는것을 내부망 웹서버의 Local File 경로를 통해 가져오는데, 외부망을 통해 가져올땐 외부망에 필터링이 있어서 이를 Raw Packet으로 HTTP Packet을 구성하여 내부망 웹서버로 직접 쏘면 LFI(Local File Include) 취약점이 발생하는 컨셉으로 할까 고민중

* 탈취된 DB Connection 정보를 토대로 mysql 서버와 직접 통신하여 mysql 원격 접속 / 쿼리 날리기까지 수행

  * 해당 과정을 위해선 mysql_native_password의 구성 원리를 이해하여야함

    ``` 
    SHA1( password ) XOR SHA1( "20-bytes random data from server" + SHA1( SHA1( password ) ) )
    ```

  * ![](https://dev.mysql.com/doc/internals/en/images/graphviz-db6c3eaf9f35f362259756b257b670e75174c29b.png)

  * [mysql internals - connection phase packets](https://dev.mysql.com/doc/internals/en/connection-phase-packets.html)

  * 또한 `sendtome`, 즉 나에게 보내기 기능이 활성화 되어야 에러없이 raw packet send의 response를 받아올 수 있기 때문에, 각 단계의 패킷마다 "sendtome" 라는 문자열이 들어가야함

  * 이를 위해선, 본래 아래와 같은 과정으로 패킷을 주고받아야함

    ![](https://arang.kr/mysql_auth_packet.png)

    0. server greeting (connection 시 서버가 전송)

    1. send login request -> receive server seed

    2. send mysql_native_password hash->receive auth ok
    3. (if password match) send mysql query -> receive query result

  * 상기 단계로 구성되는 mysql connection & query packet을 

  * sendtome라는 문자열이 각 패킷에 들어갈 수 있게 1과 2+3 두개의 패킷으로 나누고

  * 1단계와 3단계의 Packet Struture상 Packet Data의 길이에 해당하는 opcode를 변조함으로써 `TCP segment of a reassembled PDU` 를 유도함

    (2단계의 hash send 패킷에는 sendtome를 담을수 없으므로 2+3으로 묶어 패킷 전송)

  * 이를 통해 아래와 같은 과정으로 sendtome가 포함된 raw packet으로 정상 통신이 가능해짐

    * connection 시 서버가 전송하는 server greeting packet과 login request의 결과로 receive 되는 server seed, 이렇게 2개의 패킷이 첫번째 단계에서 receive 되어야함
    * 따라서 하나의 login request로 2번 receive하여야 하는데 이를 위해 TCP segment of a reassembled PDU를 유도함
    * login request 패킷의 데이터 길이에 해당하는 opcode변조 + 기존의 `program_name\x05mysql` 패킷을 `program_name\x05sendtome`로 변조 

    * (mysql -> sendtomesendtome로 변조되니 기존 패킷 길이 opcode에 11을 더함)

    * opcode상 데이터 길이상 본래 `program_name\x05sendtomesendtome` 가 전송되어야하는데 1번 단계에서 `sendtome` 만 전송되었으므로 서버는 8 character를 기다리고 있음. 따라서 sendtome만 따로 전송함으로써 TCP segment of a reassembled PDU가 유도되어 receive가 한번 더 일어나 server seed를 들고오게됨
    * 들고온 seed를 통해 mysql_native_password 계산 가능
    * SHA1( password ) XOR SHA1( "20-bytes random data from server" + SHA1( SHA1( password ) ) )
    * 계산된 mysql_native_password와 query packet을 함께 담고 query packet에서의 패킷 데이터 길이 opcode를 다시 변조(sendtome 문자열을 넣기 위함)
    * `select * from test2#sendtome` 길이만큼 패킷데이터 길이 opcode를 구성하고 2단계와 3단계 패킷을 합쳐 전송

* 위와 같은 과정으로 raw packet 구성하여 보낼 시 **flag 획득!**
* 자세한 exploit은 poc.js참조

## 추후 구현사항

 * mysql db 테이블 설계 및 구현 / init.sql 작성
 * register / login 서비스 구현
 * 외부망/내부망 서버 각각 file leak 고안
 * front 작업
 * dockerizing