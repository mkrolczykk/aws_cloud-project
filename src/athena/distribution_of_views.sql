SELECT device_type, COUNT(*) AS views
FROM views-filtered-data
GROUP BY device_type
ORDER BY views DESC;