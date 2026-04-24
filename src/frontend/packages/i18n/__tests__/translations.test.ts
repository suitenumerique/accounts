import { execSync } from 'child_process';
import fs from 'fs';

describe('checks all the frontend translation are made', () => {
  it('checks missing translation. If this test fails, go to https://crowdin.com/', () => {
    // Extract the translations
    execSync(
      'yarn extract-translation:accounts -c ./i18next-parser.config.jest.mjs',
    );
    const outputCrowdin = './locales/accounts/translations-crowdin.json';
    const jsonCrowdin = JSON.parse(fs.readFileSync(outputCrowdin, 'utf8'));
    const listKeysCrowdin = Object.keys(jsonCrowdin).sort();

    // Check the translations in the app accounts
    const outputaccounts = '../../apps/accounts/src/i18n/translations.json';
    const jsonaccounts = JSON.parse(fs.readFileSync(outputaccounts, 'utf8'));

    // Our keys are in english, so we don't need to check the english translation
    Object.keys(jsonaccounts)
      .filter((key) => key !== 'en')
      .forEach((key) => {
        const listKeysaccounts = Object.keys(
          jsonaccounts[key].translation,
        ).sort();
        const missingKeys = listKeysCrowdin.filter(
          (element) => !listKeysaccounts.includes(element),
        );
        const additionalKeys = listKeysaccounts.filter(
          (element) => !listKeysCrowdin.includes(element),
        );

        if (missingKeys.length > 0) {
          console.log(
            `Missing keys in accounts translations that should be translated in Crowdin, got to https://crowdin.com/ :`,
            missingKeys,
          );
        }

        if (additionalKeys.length > 0) {
          console.log(
            `Additional keys in accounts translations that seems not present in this branch:`,
            additionalKeys,
          );
        }

        expect(missingKeys.length).toBe(0);
      });
  });
});
