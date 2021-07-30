/*
 table user (
    primary key seq,
    id, #중복불가
    pw,
    profileImagePath,
 )


 table chat (
    primary key seq,
    from foreign key (user.id),
    to foreign key (user.id),
    date,
    msg
 )
*/