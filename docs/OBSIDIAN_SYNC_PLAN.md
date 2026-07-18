# Obsidian Sync Plan

Target output Moodle MCP untuk Obsidian **bukan** `03 Projects/Academic/Moodle`.

Gunakan folder utama:

```text
/home/zuckdorsey/Obsidian Vault/Academic/Moodle/
```

Struktur target Phase 2:

```text
Academic/Moodle/
├── Dashboard.md
├── Deadlines.md
├── Grades.md
├── Courses/
├── Assignments/
└── Materials/
```

Catatan implementasi:

- Root dapat dioverride lewat env `MOODLE_OBSIDIAN_SYNC_DIR`.
- Jika env tidak ada, gunakan `${OBSIDIAN_VAULT_PATH}/Academic/Moodle`.
- Jangan menulis output Moodle ke `03 Projects/`.
