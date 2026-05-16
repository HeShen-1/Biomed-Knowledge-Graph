module.exports = {
  root: true,
  env: { browser: true, es2022: true },
  extends: [],
  rules: {
    'import/no-restricted-paths': [
      'error',
      {
        zones: [
          { target: './src/components', from: './src/api', message: 'Components must not import from api/' },
          { target: './src/components', from: './src/store', message: 'Components must use props, not stores' },
        ],
      },
    ],
  },
};
