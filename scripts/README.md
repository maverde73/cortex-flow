# Scripts Directory

This directory contains utility shell scripts for managing the Cortex Flow system.

## Available Scripts

### `start_all.sh`
Starts all configured agents based on `.env` configuration.

**Usage:**
```bash
./scripts/start_all.sh
```

**What it does:**
- Reads `ENABLED_AGENTS` from `.env`
- Starts only configured agents
- Performs health checks
- Saves PIDs to `logs/` directory

**Configuration:**
Edit `.env` to control which agents start:
```bash
ENABLED_AGENTS=researcher,analyst,writer  # All agents
ENABLED_AGENTS=researcher                  # Only researcher
```

---

### `stop_all.sh`
Stops all running agent servers.

**Usage:**
```bash
./scripts/stop_all.sh
```

**What it does:**
- Kills processes from saved PIDs
- Falls back to killing by process name
- Cleans up PID files

---

### `show_structure.sh`
Displays project structure and statistics.

**Usage:**
```bash
./scripts/show_structure.sh
```

**What it shows:**
- Directory tree
- File counts by type
- Total lines of code
- Quick command reference

---

## Adding New Scripts

When creating new utility scripts:

1. Place them in this directory
2. Make them executable: `chmod +x scripts/new_script.sh`
3. Use bash shebang: `#!/bin/bash`
4. Add documentation in this README
5. Update `.gitignore` if needed

**Example:**
```bash
# Create new script
touch scripts/backup.sh
chmod +x scripts/backup.sh

# Add shebang and code
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
# Backup configuration and logs
tar -czf backup-$(date +%Y%m%d).tar.gz .env logs/
EOF
```

## Notes

- All scripts should be idempotent when possible
- Use proper error handling (`set -e` for fail-fast)
- Provide user feedback (echo messages)
- Document environment dependencies
