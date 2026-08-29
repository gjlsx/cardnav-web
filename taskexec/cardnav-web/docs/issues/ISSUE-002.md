# ISSUE-002 [P1]

This site does not support Russian. Drop `README.ru.md` and the tests that required it.

## Changes

- Delete `README.ru.md`
- Remove the Russian README language-switcher links
- Record in Chinese and English READMEs that the site does not support Russian
- Stop `test/public-brand.test.ts` from reading `README.ru.md`

## Verify

- `README.ru.md` does not exist
- `pnpm exec tsx --test test/public-brand.test.ts` passes
- Chinese and English READMEs still carry the centralized public contacts
