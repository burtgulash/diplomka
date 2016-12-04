drop table if exists csfd_filmy;
create table csfd_filmy (
    film_id serial primary key,
    title text not null
);

-- https://www.postgresql.org/message-id/flat/CAANrE7rpWjvZgdKX_hArNp8ynUezZ-Ehp8QEqC7hwfXuNqa91g@mail.gmail.com#CAANrE7rpWjvZgdKX_hArNp8ynUezZ-Ehp8QEqC7hwfXuNqa91g@mail.gmail.com
create or replace function unaccent_text(text)
    returns text as
$BODY$
    SELECT unaccent($1)
$BODY$
    language sql immutable
    cost 1;

create index csfd_filmy_trgm_trgm_idx
          on csfd_filmy
       using gin (lower(unaccent_text(title)) gin_trgm_ops);
