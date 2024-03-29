SELECT item_id, ROUND(AVG(review_stars), 2) AS rating_average
FROM (
         SELECT *
         FROM sagemaker_output
         WHERE review_title IS NOT NULL AND review_text IS NOT NULL
     )
GROUP BY item_id
ORDER BY rating_average DESC;