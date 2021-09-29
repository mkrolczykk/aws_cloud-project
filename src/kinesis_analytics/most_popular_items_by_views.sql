CREATE OR REPLACE STREAM "items_output_stream" (
    item_id VARCHAR(10),
    total_views INTEGER
);

CREATE OR REPLACE PUMP "ITEMS_STREAM_PUMP" AS
    INSERT INTO "items_output_stream"
        SELECT STREAM *
        FROM TABLE (
            TOP_K_ITEMS_TUMBLING(
                CURSOR(
                    SELECT STREAM * FROM "firehouse_views_delivery_stream_001"
                ),
                'item_id',
                10,
                60
            )
        );