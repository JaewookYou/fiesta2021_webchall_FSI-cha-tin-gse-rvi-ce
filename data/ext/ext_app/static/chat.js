
	function getDateStr(strdate){
		date = new Date(strdate);
		return `${date.getHours().toString().padStart(2,"0")}:${date.getMinutes().toString().padStart(2,"0")} | ${date.toDateString().split(" ")[1]} ${date.getDate()}`
	}

	function getRandomSID(){
		var sid = ""
		for(var i=0; i<32; i++){
			sid += Math.floor(Math.random()*16).toString(16)
		}
		return sid
	}

  function getCookie(name) {
      var value = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
      return value? value[2] : null;
  }

  function maketime(){
  	var date = new Date().toISOString();
  	var a = date.split('T')[0];
  	var b = date.split('T')[1].split('.')[0];
  	return `${a} ${b}`
  }
	
	function getBase64(file) {
	  return new Promise((resolve, reject) => {
	    const reader = new FileReader();
	    reader.readAsDataURL(file);
	    reader.onload = () => resolve(reader.result);
	    reader.onerror = error => reject(error);
	  });
	}

	function appendMessages(data){
		var appendHTML = "";			
		var datestr = getDateStr(data.date)
		data.msg = eval(`data.msg='${data.msg}'`);
		if (data.to == userid && data.to != data.from){
			appendHTML += `<div class="incoming_msg">
              <div class="incoming_msg_img"> <img src="${profileImage}"> </div>
              <div class="received_msg">
                <div class="received_withd_msg">
                  <p>${data.msg}</p>
                  <span class="time_date"> ${datestr}</span></div>
              </div>
            </div>
            `
    } else if (data.from == userid || data.from == data.to) {
    	appendHTML += `<div class="outgoing_msg">
          <div class="sent_msg">
            <p>${data.msg}</p>
            <span class="time_date"> ${datestr}</span> </div>
        </div>
        `
    } else {
    	console.log("[x] ?? what's going on?");
    }
	  	
		
		$(".msg_history").append(appendHTML);
		$(".msg_history").scrollTop($(".msg_history")[0].scrollHeight);
	}

	function getlist(){
		// get chatting lists
		var data = {
			"command": "getlist",
			"from": userid
		};

		sock.emit("getlist", data);
	}

	function getchatmsg(id){
		// get chatting messages
		var data = {
			"command": "getchatmsg",
			"from": userid,
			"to": focusedUser
		};

		sock.emit("getchatmsg", data);
	}

	async function getmessage(id){
		focusedUser = id;
		profileImage = await getProfileImage(focusedUser);

		$(".active_chat").attr("class", $(".active_chat").attr("class").replace(" active_chat",""));
		$(`.chat_list.${id}`).attr("class",`chat_list ${id} active_chat`);
		if(getchatmsg(id) == false){
			alert("getchatmsg error");
		}
		$("#sendto").val(id);
	}

  async function getProfileImage(id) {
  	profileImage = localStorage.getItem(id)
		if(profileImage == null){
			profileImage = await fetch("/getProfileImage?id="+id).then(r=>r.text()).then(r=>{return r});
			localStorage.setItem(id,profileImage)
		}
		return profileImage
  }

	async function doUpload(fis){
		var f = $("#file1")[0].files[0];
		var encodedFile = await getBase64(f);

		var data = {
			"command": "imagesend",
			"date": maketime(),
			"from": userid,
			"to": focusedUser,
			"content": encodedFile,
			"filename": f.name

		};

		if(data["to"] == userid){
			data["sendtome"] = 'true';
		}

		sock.emit("imagesend", data);

	}

	function roomadd(chatto){
		var data = {
			"command": "roomadd",
			"from": userid,
			"to": chatto
		}

		sock.emit("roomadd", data);
	}
