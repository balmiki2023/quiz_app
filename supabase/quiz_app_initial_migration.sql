-- ============================================================
-- Quiz App — CURRENT DATABASE CLEAN REBUILD
-- Generated from the current schema established in the project.
--
-- WARNING:
-- This migration is destructive. It drops the current Quiz App
-- objects in public and recreates them.
--
-- This file recreates DATABASE STRUCTURE and application logic.
-- It does NOT recreate the existing quiz/question DATA because
-- the complete current data set was not provided as an authoritative
-- database dump.
--
-- Current ID model:
--   categories.id  -> text  (ch_01, ch_02, ...)
--   quizzes.id      -> text  (qz_01, qz_02, ...)
--   questions.id    -> text  (q_01, q_02, ...)
-- ============================================================

begin;

-- ============================================================
-- 0. CLEAN CURRENT QUIZ-APP OBJECTS
-- ============================================================

-- Remove the auth trigger before dropping its function.
drop trigger if exists on_auth_user_created on auth.users;

-- Drop tables first because their RLS policies depend on helper
-- functions such as public.is_admin().
drop table if exists public.user_answers cascade;
drop table if exists public.quiz_attempts cascade;
drop table if exists public.question_statistics cascade;
drop table if exists public.subscription_sessions cascade;
drop table if exists public.device_users cascade;
drop table if exists public.subscriptions cascade;
drop table if exists public.quiz_questions cascade;
drop table if exists public.quiz_answers cascade;
drop table if exists public.questions cascade;
drop table if exists public.quizzes cascade;
drop table if exists public.categories cascade;
drop table if exists public.profiles cascade;

-- Drop functions after dependent tables/policies are gone.
drop function if exists public.update_question_statistics();
drop function if exists public.release_subscription_session();
drop function if exists public.claim_subscription_session(text);
drop function if exists public.claim_device_user(text);
drop function if exists public.activate_subscription(uuid);
drop function if exists public.is_admin();
drop function if exists public.handle_new_user();

-- ============================================================
-- 1. PROFILES
-- ============================================================

create table public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text,
    avatar_url text,
    is_admin boolean default false,
    created_at timestamptz default now()
);

-- ============================================================
-- 2. CATEGORIES
-- ============================================================

create table public.categories (
    id text primary key,
    name text not null,
    description text,
    image_url text,
    is_premium boolean default false,
    is_published boolean default true,
    created_at timestamptz default now()
);

-- ============================================================
-- 3. QUIZZES
-- ============================================================

create table public.quizzes (
    id text primary key,
    category_id text references public.categories(id) on delete cascade,
    title text not null,
    description text,
    difficulty text,
    is_premium boolean default false,
    is_published boolean default false,
    time_limit_seconds integer,
    created_at timestamptz default now()
);

-- ============================================================
-- 4. QUESTIONS
-- ============================================================
-- Questions are independent entities.
-- quiz_id/question_order are retained for compatibility with
-- the evolved application/database, but quiz membership is
-- primarily represented by quiz_questions.

create table public.questions (
    id text primary key,
    quiz_id text references public.quizzes(id) on delete cascade,
    question_text text not null,
    explanation text,
    question_order integer,
    created_at timestamptz default now(),

    option_a text,
    option_b text,
    option_c text,
    option_d text,
    correct_option text,

    category_id text references public.categories(id)
);

-- ============================================================
-- 5. QUIZ QUESTIONS
-- ============================================================
-- Many-to-many relationship:
-- one question can be assigned to multiple quizzes.

create table public.quiz_questions (
    quiz_id text not null
        references public.quizzes(id) on delete cascade,
    question_id text not null
        references public.questions(id) on delete cascade,
    question_order integer not null,
    created_at timestamptz not null default now(),

    primary key (quiz_id, question_id),
    unique (quiz_id, question_order)
);

-- ============================================================
-- 6. LEGACY QUIZ ANSWERS
-- ============================================================
-- Retained because the original schema and user_answers model
-- still reference this table.

create table public.quiz_answers (
    id uuid primary key default gen_random_uuid(),
    question_id text references public.questions(id) on delete cascade,
    answer_text text not null,
    is_correct boolean default false,
    answer_order integer
);

-- ============================================================
-- 7. QUIZ ATTEMPTS
-- ============================================================
-- quiz_id is nullable because random quizzes do not have a
-- corresponding row in quizzes.

create table public.quiz_attempts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.profiles(id) on delete cascade,
    quiz_id text references public.quizzes(id) on delete cascade,
    score integer default 0,
    total_questions integer not null,
    correct_answers integer default 0,
    time_taken_seconds integer,
    completed_at timestamptz default now(),
    answers jsonb not null default '[]'::jsonb
);

-- ============================================================
-- 8. USER ANSWERS
-- ============================================================

create table public.user_answers (
    id uuid primary key default gen_random_uuid(),
    attempt_id uuid references public.quiz_attempts(id) on delete cascade,
    question_id text references public.questions(id) on delete cascade,
    selected_answer_id uuid references public.quiz_answers(id),
    is_correct boolean not null
);

-- ============================================================
-- 9. SUBSCRIPTIONS
-- ============================================================

create table public.subscriptions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid unique references public.profiles(id) on delete cascade,
    status text default 'free',
    provider text,
    provider_customer_id text,
    provider_subscription_id text,
    current_period_end timestamptz,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- ============================================================
-- 10. DEVICE OWNERSHIP
-- ============================================================
-- Normal users: one persistent device -> one user.
-- Admins are exempt through claim_device_user().

create table public.device_users (
    device_session_id text primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    created_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now()
);

-- ============================================================
-- 11. PREMIUM SUBSCRIPTION SESSIONS
-- ============================================================
-- One Premium account may have one active Premium device session.

create table public.subscription_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    device_session_id text not null,
    created_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now()
);

create unique index subscription_sessions_user_id_idx
on public.subscription_sessions(user_id);

-- ============================================================
-- 12. QUESTION STATISTICS
-- ============================================================

create table public.question_statistics (
    question_id text primary key
        references public.questions(id) on delete cascade,
    total_attempts integer not null default 0,
    correct_answers integer not null default 0,
    correct_rate numeric(5,4) not null default 0,
    updated_at timestamptz not null default now()
);

-- ============================================================
-- 13. INDEXES
-- ============================================================

create index quizzes_category_id_idx
on public.quizzes(category_id);

create index questions_category_id_idx
on public.questions(category_id);

create index questions_quiz_id_idx
on public.questions(quiz_id);

create index quiz_questions_question_id_idx
on public.quiz_questions(question_id);

create index quiz_answers_question_id_idx
on public.quiz_answers(question_id);

create index quiz_attempts_user_id_idx
on public.quiz_attempts(user_id);

create index quiz_attempts_quiz_id_idx
on public.quiz_attempts(quiz_id);

create index user_answers_attempt_id_idx
on public.user_answers(attempt_id);

create index user_answers_question_id_idx
on public.user_answers(question_id);

create index subscription_sessions_device_session_id_idx
on public.subscription_sessions(device_session_id);

-- ============================================================
-- 14. NEW AUTH USER -> PROFILE
-- ============================================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (
        id,
        display_name
    )
    values (
        new.id,
        new.raw_user_meta_data->>'display_name'
    );

    return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();

-- ============================================================
-- 15. ADMIN HELPER
-- ============================================================

create or replace function public.is_admin()
returns boolean
language sql
security definer
set search_path = public
stable
as $$
    select exists (
        select 1
        from public.profiles
        where id = auth.uid()
          and is_admin = true
    );
$$;

grant execute on function public.is_admin()
to authenticated;

-- ============================================================
-- 16. DEVICE OWNERSHIP RPC
-- ============================================================

create or replace function public.claim_device_user(
    target_device_session_id text
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
    current_user_id uuid;
    existing_user_id uuid;
    current_is_admin boolean;
begin
    current_user_id := auth.uid();

    if current_user_id is null then
        raise exception 'Not authenticated';
    end if;

    select is_admin
    into current_is_admin
    from public.profiles
    where id = current_user_id;

    -- Admins can use any device.
    if current_is_admin = true then
        return true;
    end if;

    select user_id
    into existing_user_id
    from public.device_users
    where device_session_id = target_device_session_id
    for update;

    if existing_user_id is null then
        insert into public.device_users (
            device_session_id,
            user_id,
            created_at,
            last_seen_at
        )
        values (
            target_device_session_id,
            current_user_id,
            now(),
            now()
        );

        return true;
    end if;

    if existing_user_id = current_user_id then
        update public.device_users
        set last_seen_at = now()
        where device_session_id = target_device_session_id;

        return true;
    end if;

    return false;
end;
$$;

grant execute on function public.claim_device_user(text)
to authenticated;

-- ============================================================
-- 17. PREMIUM DEVICE SESSION RPC
-- ============================================================

create or replace function public.claim_subscription_session(
    target_device_session_id text
)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
    current_user_id uuid;
    existing_session text;
begin
    current_user_id := auth.uid();

    if current_user_id is null then
        raise exception 'Not authenticated';
    end if;

    select device_session_id
    into existing_session
    from public.subscription_sessions
    where user_id = current_user_id
    for update;

    if existing_session is null then
        insert into public.subscription_sessions (
            user_id,
            device_session_id,
            created_at,
            last_seen_at
        )
        values (
            current_user_id,
            target_device_session_id,
            now(),
            now()
        );

        return true;
    end if;

    if existing_session = target_device_session_id then
        update public.subscription_sessions
        set last_seen_at = now()
        where user_id = current_user_id;

        return true;
    end if;

    return false;
end;
$$;

grant execute on function public.claim_subscription_session(text)
to authenticated;

create or replace function public.release_subscription_session()
returns boolean
language plpgsql
security definer
set search_path = public
as $$
begin
    if auth.uid() is null then
        raise exception 'Not authenticated';
    end if;

    delete from public.subscription_sessions
    where user_id = auth.uid();

    return true;
end;
$$;

grant execute on function public.release_subscription_session()
to authenticated;

-- ============================================================
-- 18. SUBSCRIPTION ACTIVATION RPC
-- ============================================================
-- Admin/service-side activation helper used by the application.
-- The application calls this only for the currently authenticated
-- user.

create or replace function public.activate_subscription(
    target_user_id uuid
)
returns public.subscriptions
language plpgsql
security definer
set search_path = public
as $$
declare
    result public.subscriptions;
begin
    if auth.uid() is null then
        raise exception 'Not authenticated';
    end if;

    if auth.uid() <> target_user_id
       and not public.is_admin() then
        raise exception 'Not authorized';
    end if;

    insert into public.subscriptions (
        user_id,
        status,
        updated_at
    )
    values (
        target_user_id,
        'active',
        now()
    )
    on conflict (user_id)
    do update set
        status = 'active',
        updated_at = now()
    returning * into result;

    return result;
end;
$$;

grant execute on function public.activate_subscription(uuid)
to authenticated;

-- ============================================================
-- 19. QUESTION STATISTICS RPC
-- ============================================================

create or replace function public.update_question_statistics()
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.question_statistics (
        question_id,
        total_attempts,
        correct_answers,
        correct_rate,
        updated_at
    )
    select
        first_answers.question_id,
        count(*),
        count(*) filter (
            where first_answers.is_correct = true
        ),
        round(
            avg(
                case
                    when first_answers.is_correct = true
                    then 1.0
                    else 0.0
                end
            ),
            4
        ),
        now()
    from (
        select distinct on (
            qa.user_id,
            answer->>'question_id'
        )
            qa.user_id,
            answer->>'question_id' as question_id,
            (answer->>'is_correct')::boolean as is_correct
        from public.quiz_attempts qa
        cross join lateral jsonb_array_elements(
            qa.answers
        ) as answer
        where qa.user_id is not null
          and answer->>'selected_option' is not null
        order by
            qa.user_id,
            answer->>'question_id',
            qa.completed_at asc,
            qa.id asc
    ) as first_answers
    where exists (
        select 1
        from public.questions q
        where q.id = first_answers.question_id
    )
    group by first_answers.question_id
    on conflict (question_id)
    do update set
        total_attempts = excluded.total_attempts,
        correct_answers = excluded.correct_answers,
        correct_rate = excluded.correct_rate,
        updated_at = now();
end;
$$;

-- ============================================================
-- 20. ROW LEVEL SECURITY
-- ============================================================

alter table public.profiles enable row level security;
alter table public.categories enable row level security;
alter table public.quizzes enable row level security;
alter table public.questions enable row level security;
alter table public.quiz_questions enable row level security;
alter table public.quiz_answers enable row level security;
alter table public.quiz_attempts enable row level security;
alter table public.user_answers enable row level security;
alter table public.subscriptions enable row level security;
alter table public.device_users enable row level security;
alter table public.subscription_sessions enable row level security;
alter table public.question_statistics enable row level security;

-- ============================================================
-- 21. PUBLIC CATEGORY ACCESS
-- ============================================================

create policy "Anyone can view published categories"
on public.categories
for select
to public
using (is_published = true);

-- ============================================================
-- 22. PUBLIC QUIZ ACCESS
-- ============================================================

create policy "Anyone can view published quizzes"
on public.quizzes
for select
to public
using (is_published = true);

-- ============================================================
-- 23. PUBLIC QUESTION ACCESS
-- ============================================================
-- Questions are visible when they belong to a published quiz
-- through quiz_questions.

create policy "Anyone can view questions from published quizzes"
on public.questions
for select
to public
using (
    exists (
        select 1
        from public.quiz_questions qq
        join public.quizzes q
            on q.id = qq.quiz_id
        where qq.question_id = questions.id
          and q.is_published = true
    )
);

-- ============================================================
-- 24. PUBLIC QUIZ-QUESTION RELATIONSHIP ACCESS
-- ============================================================

create policy "Anyone can view published quiz questions"
on public.quiz_questions
for select
to public
using (
    exists (
        select 1
        from public.quizzes q
        where q.id = quiz_questions.quiz_id
          and q.is_published = true
    )
);

-- ============================================================
-- 25. PUBLIC ANSWER ACCESS
-- ============================================================

create policy "Anyone can view answers from published quizzes"
on public.quiz_answers
for select
to public
using (
    exists (
        select 1
        from public.questions question
        join public.quiz_questions qq
            on qq.question_id = question.id
        join public.quizzes quiz
            on quiz.id = qq.quiz_id
        where question.id = quiz_answers.question_id
          and quiz.is_published = true
    )
);

-- ============================================================
-- 26. PROFILE ACCESS
-- ============================================================

create policy "Users can view their own profile"
on public.profiles
for select
to authenticated
using (id = auth.uid());

create policy "Users can create their own profile"
on public.profiles
for insert
to authenticated
with check (id = auth.uid());

create policy "Users can update their own profile"
on public.profiles
for update
to authenticated
using (id = auth.uid())
with check (id = auth.uid());

-- ============================================================
-- 27. QUIZ ATTEMPTS
-- ============================================================

create policy "Users can create their own quiz attempts"
on public.quiz_attempts
for insert
to authenticated
with check (user_id = auth.uid());

create policy "Users can view their own quiz attempts"
on public.quiz_attempts
for select
to authenticated
using (user_id = auth.uid());

-- ============================================================
-- 28. USER ANSWERS
-- ============================================================

create policy "Users can create their own user answers"
on public.user_answers
for insert
to authenticated
with check (
    exists (
        select 1
        from public.quiz_attempts attempt
        where attempt.id = user_answers.attempt_id
          and attempt.user_id = auth.uid()
    )
);

create policy "Users can view their own user answers"
on public.user_answers
for select
to authenticated
using (
    exists (
        select 1
        from public.quiz_attempts attempt
        where attempt.id = user_answers.attempt_id
          and attempt.user_id = auth.uid()
    )
);

-- ============================================================
-- 29. SUBSCRIPTIONS
-- ============================================================

create policy "Users can view their own subscription"
on public.subscriptions
for select
to authenticated
using (user_id = auth.uid());

-- ============================================================
-- 30. QUESTION STATISTICS
-- ============================================================

create policy "Anyone can view question statistics"
on public.question_statistics
for select
to public
using (true);

-- ============================================================
-- 31. ADMIN ACCESS
-- ============================================================

create policy "Admins can view all categories"
on public.categories
for select
to authenticated
using (public.is_admin());

create policy "Admins can insert categories"
on public.categories
for insert
to authenticated
with check (public.is_admin());

create policy "Admins can update categories"
on public.categories
for update
to authenticated
using (public.is_admin())
with check (public.is_admin());

create policy "Admins can delete categories"
on public.categories
for delete
to authenticated
using (public.is_admin());

create policy "Admins can view all quizzes"
on public.quizzes
for select
to authenticated
using (public.is_admin());

create policy "Admins can insert quizzes"
on public.quizzes
for insert
to authenticated
with check (public.is_admin());

create policy "Admins can update quizzes"
on public.quizzes
for update
to authenticated
using (public.is_admin())
with check (public.is_admin());

create policy "Admins can delete quizzes"
on public.quizzes
for delete
to authenticated
using (public.is_admin());

create policy "Admins can view all questions"
on public.questions
for select
to authenticated
using (public.is_admin());

create policy "Admins can insert questions"
on public.questions
for insert
to authenticated
with check (public.is_admin());

create policy "Admins can update questions"
on public.questions
for update
to authenticated
using (public.is_admin())
with check (public.is_admin());

create policy "Admins can delete questions"
on public.questions
for delete
to authenticated
using (public.is_admin());

create policy "Admins can manage quiz questions"
on public.quiz_questions
for all
to authenticated
using (public.is_admin())
with check (public.is_admin());

create policy "Admins can view all quiz attempts"
on public.quiz_attempts
for select
to authenticated
using (public.is_admin());

create policy "Admins can view all subscriptions"
on public.subscriptions
for select
to authenticated
using (public.is_admin());

-- ============================================================
-- 32. DATA SEED — CURRENT CATEGORIES
-- ============================================================
-- These are the current category IDs established in the app.
-- Quiz/question rows are intentionally not seeded here because
-- the complete current question bank was not supplied as a
-- canonical data dump.

insert into public.categories (
    id,
    name,
    is_premium,
    is_published
)
values
    ('ch_01', 'General Knowledge', false, true),
    ('ch_02', 'History', false, true),
    ('ch_03', 'Science', false, true),
    ('ch_04', 'Technology', false, true),
    ('ch_05', 'Geography', false, true),
    ('ch_06', 'Biology', false, true),
    ('ch_07', 'Algae', false, true)
on conflict (id) do update set
    name = excluded.name,
    is_published = excluded.is_published;

commit;

-- ============================================================
-- END OF CURRENT DATABASE REBUILD
-- ============================================================
