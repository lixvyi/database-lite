PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  isbn TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT '其他',
  publisher TEXT NOT NULL DEFAULT '',
  total_copies INTEGER NOT NULL DEFAULT 1 CHECK(total_copies >= 0),
  available_copies INTEGER NOT NULL DEFAULT 1 CHECK(available_copies >= 0 AND available_copies <= total_copies),
  shelf_code TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS readers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  card_no TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  phone TEXT NOT NULL DEFAULT '',
  department TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT '正常' CHECK(status IN ('正常', '停用')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  loan_no TEXT NOT NULL UNIQUE,
  book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE RESTRICT,
  reader_id INTEGER NOT NULL REFERENCES readers(id) ON DELETE RESTRICT,
  borrowed_at TEXT NOT NULL,
  due_at TEXT NOT NULL,
  returned_at TEXT,
  status TEXT NOT NULL DEFAULT '借阅中' CHECK(status IN ('借阅中', '已归还')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_readers_name ON readers(name);
CREATE INDEX IF NOT EXISTS idx_loans_status_due ON loans(status, due_at);

