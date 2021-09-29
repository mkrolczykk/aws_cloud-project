CREATE OR REPLACE STREAM "categories_output_stream" (
    category VARCHAR(50),
    total_views INTEGER
);

CREATE OR REPLACE PUMP "CATEGORIES_STREAM_PUMP" AS
    INSERT INTO "categories_output_stream"
        SELECT STREAM *
        FROM TABLE (
            TOP_K_ITEMS_TUMBLING(
                CURSOR(
                    SELECT STREAM *
                    FROM "firehouse_views_delivery_stream_001" AS f
                    JOIN "items_information" AS i
                    ON f."item_id" = i."item_id"
                ),
                'category',
                10,
                60
            )
        );
