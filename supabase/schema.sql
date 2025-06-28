-- Projects: Gemini API keys
create table if not exists projects (
  id uuid primary key default uuid_generate_v4(),
  name text,
  region text,
  api_key text,
  token_limit int default 250000,
  tokens_used int default 0,
  active boolean default true,
  last_used_at timestamptz
);

-- Users: Telegram admins and (optionally) end users
create table if not exists users (
  id uuid primary key default uuid_generate_v4(),
  telegram_id bigint,
  is_admin boolean default false,
  created_at timestamptz default now()
);

-- Usage logs: Track API usage per project/user
create table if not exists usage_logs (
  id uuid primary key default uuid_generate_v4(),
  project_id uuid references projects(id),
  user_id uuid references users(id),
  prompt_tokens int,
  response_tokens int,
  total_tokens int,
  timestamp timestamptz default now()
);

-- User API keys: For your customers
create table if not exists user_api_keys (
  id uuid primary key default uuid_generate_v4(),
  key text unique,
  user_label text,
  active boolean default true,
  created_at timestamptz default now()
);

-- Bots: Registered bots
create table if not exists bots (
  id uuid primary key default uuid_generate_v4(),
  name text,
  token text,
  status text default 'active',
  base_prompt text,
  api_key_id uuid references user_api_keys(id),
  created_at timestamptz default now()
); 