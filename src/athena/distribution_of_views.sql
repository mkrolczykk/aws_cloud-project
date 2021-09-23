SELECT device_type, COUNT(*) AS views
FROM views_filtered_data
GROUP BY device_type
ORDER BY views DESC;