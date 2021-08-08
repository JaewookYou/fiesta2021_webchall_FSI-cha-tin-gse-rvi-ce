/* if do initializing, use this
drop table chatdb.user, chatdb.chatroom, chatdb.chat, chatdb.flag;
drop database chatdb;
*/

create database chatdb;
use chatdb;

create user 'chatdb_admin'@'%' identified by 'th1s_1s_ch4tdb_4dm1n_p4ssw0rd';

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

insert into flag values("fiesta{mysql_int3rner_1s_s0_fun_isnt_1t?}");
insert into user (userid, userpw, userProfileImagePath) values("welcomebot", "th1s_1s_w3lc0me_b0t_p4ssw0rd", "welcomebot.png");

grant select, insert on chatdb.user to 'chatdb_admin'@'%';
grant select, insert, update on chatdb.chatroom to 'chatdb_admin'@'%';
grant select, insert on chatdb.chat to 'chatdb_admin'@'%';
grant select on chatdb.flag to 'chatdb_admin'@'%';
flush privileges;

