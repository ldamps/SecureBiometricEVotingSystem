/** @param {import('webpack').Configuration} config */
module.exports = function override(config) {
  // face-api.js (ES build) references Node's `fs` inside a try/catch; webpack 5 must not try to bundle it.
  config.resolve.fallback = {
    ...(config.resolve.fallback || {}),
    fs: false,
    path: false,
  };

  const smRule = config.module.rules.find(
    (rule) =>
      rule &&
      rule.enforce === "pre" &&
      rule.loader &&
      String(rule.loader).includes("source-map-loader")
  );
  if (smRule && smRule.exclude) {
    smRule.exclude = Array.isArray(smRule.exclude)
      ? [...smRule.exclude, /face-api\.js/]
      : [smRule.exclude, /face-api\.js/];
  }

  config.ignoreWarnings = [
    ...(config.ignoreWarnings || []),
    (warning) =>
      warning.module &&
      /node_modules\/react-datepicker/.test(String(warning.module.resource)) &&
      /Critical dependency/.test(String(warning.message)),
  ];

  return config;
};
