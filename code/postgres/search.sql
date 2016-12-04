select 
  1 / similarity(title, lower(unaccent_text(:query))) as score
  , title
  from csfd_filmy
 where lower(unaccent_text(title)) % :query
order by score desc, title
limit 100;
