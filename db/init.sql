drop table chatdb.user, chatdb.chatroom, chatdb.chat, chatdb.flag;
drop database chatdb;

create database chatdb;
use chatdb;

create user 'arangtest'@'%' identified by 'testpass';

create table user (
   userseq int not null auto_increment primary key,
   userid varchar(50), 
   userpw varchar(50),
   userProfileImagePath varchar(255)
) default character set utf8 collate utf8_general_ci;

create table chatroom (
   roomseq int not null auto_increment primary key,
   user_a varchar(50),
   user_b varchar(50),
   lastmsg varchar(1000),
   lastdate datetime
) default character set utf8 collate utf8_general_ci;

create table chat (
   chatseq int not null auto_increment primary key,
   chatfrom varchar(50),
   chatto varchar(50),
   chatmsg varchar(1000),
   chatdate datetime,
   isImage boolean default false
) default character set utf8 collate utf8_general_ci;

create table flag (
   flag varchar(255)
) default character set utf8 collate utf8_general_ci;

insert into flag values("fiesta{this_is_test_flag}");
insert into user (userid, userpw, userProfileImagePath) values("admin", "admin", "admin.png");
insert into user (userid, userpw, userProfileImagePath) values("guest", "guest", "guest.png");

insert into chatroom (user_a, user_b, lastmsg, lastdate) values("admin", "guest", "lastmsg", "2021-08-06 23:48:00");
insert into chat (chatfrom, chatto, chatmsg, chatdate) values("admin", "guest", "firstmsg", "2021-08-06 23:47:00");
insert into chat (chatfrom, chatto, chatmsg, chatdate) values("guest", "admin", "secondmsg", "2021-08-06 23:47:30"));
insert into chat (chatfrom, chatto, chatmsg, chatdate) values("admin", "guest", "lastmsg", "2021-08-06 23:48:00");

insert into chatroom (user_a, user_b, lastmsg, lastdate) values("admin", "admin", "lastmsg", "2021-08-06 23:48:00");
insert into chat (chatfrom, chatto, chatmsg, chatdate) values("admin", "admin", "self msg", "2021-08-06 23:47:00");

grant select, insert on chatdb.user to 'arangtest'@'%';
grant select, insert, update on chatdb.chatroom to 'arangtest'@'%';
grant select, insert on chatdb.chat to 'arangtest'@'%';
grant select on chatdb.flag to 'arangtest'@'%';
flush privileges;



/*

drop table chatdb.user, chatdb.chatroom, chatdb.chat, chatdb.flag;
drop database chatdb;

*/