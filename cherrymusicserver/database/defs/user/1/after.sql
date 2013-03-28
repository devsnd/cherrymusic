CREATE TRIGGER IF NOT EXISTS trigger_users_after_update_set_modified
    AFTER UPDATE ON users
    FOR EACH ROW
    BEGIN
        UPDATE users SET _modified=(strftime('%s', 'now')) WHERE _id = new._id;
    END;
