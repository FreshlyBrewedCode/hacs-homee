const fs = require("fs");
const path = require("path");

const manifestPath = path.resolve(process.argv[2]);
const m = require(manifestPath);

m.version = process.argv[3];
fs.writeFileSync(manifestPath, JSON.stringify(m, null, 4), {
    encoding: "utf8",
    flag: "w",
});
