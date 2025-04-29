-- SQL-запрос: 10 пользователей с максимальным количеством сохранённых ссылок
-- При равенстве количества — сначала те, кто раньше зарегистрирован

SELECT u.id, u.email, COUNT(l.id) AS links_count, u.created_at
FROM users u
LEFT JOIN links l ON l.user_id = u.id
GROUP BY u.id
ORDER BY links_count DESC, u.created_at ASC
LIMIT 10; 