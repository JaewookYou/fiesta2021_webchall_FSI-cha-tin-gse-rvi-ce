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
   chatdate datetime
) default character set utf8 collate utf8_general_ci;

create table flag (
   flag varchar(255)
) default character set utf8 collate utf8_general_ci;

insert into flag values("fiesta{this_is_test_flag}");
insert into user values(null, "admin", "admin", "/tmp/a.jpg");

grant select, insert on chatdb.user to 'arangtest'@'%';
grant select, insert, update on chatdb.chatroom to 'arangtest'@'%';
grant select, insert on chatdb.chat to 'arangtest'@'%';
grant select on chatdb.flag to 'arangtest'@'%';
flush privileges;



/*

drop table chatdb.user, chatdb.chatroom, chatdb.chat, chatdb.flag;
drop database chatdb;

*/