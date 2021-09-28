SELECT device_type, COUNT(*) AS total_views
FROM views
GROUP BY device_type
ORDER BY total_views DESC;