create table users(
    id integer primary key autoincrement,
    username text unique not null,
    email text unique not null,
    password text not null
);
create table notes(
    id integer primary key autoincrement,
    user_id integer not null,
    title text not null,
    content text not null,
    created_at datetime default current_timestamp,
    updated_at datetime default current_timestamp,
    foreign key (user_id) references users(id)
);