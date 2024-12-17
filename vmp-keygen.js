const { createKeyGen } = require("vmprotect-keygen");
const { Command } = require("commander");
const program = new Command();

// TODO: Еще какие-то данные нужно занести или чет такое, пишет INVALID_KEY, надо отладку сделать нормальную

program
  .requiredOption("-u, --userName <userName>", "")  // Required argument for userName
  .option("-e, --email <email>", "User email", "")
  .option("-x, --expDate <expDate>", "Expiration date in ISO format", "")
  .option("-m, --maxBuildDate <maxBuildDate>", "Max build date in ISO format", "")
  .option("-r, --runningTimeLimit <runningTimeLimit>", "Running time limit in minutes", 0)
  .option("-h, --hardwareId <hardwareId>", "Hardware ID in base64 format", "")
  .option("-d, --userData <userData>", "User data in base64 format", "");

program.parse(process.argv);
const { userName, email, expDate, maxBuildDate, runningTimeLimit, hardwareId, userData } = program.opts();

const exported_algorithm = "RSA";
const exported_bits = 2048;
const exported_private = "betSWjZocRwOkA1WvHnJ3GYbDl/w7vRNsAbXSNYsWwK7AjRT7/zcCt0uQ9K4KeWCd2BOD22eoLCqNx/owDd1gEJTvoGQh8twzz1FxcKBil9hHfc4lnZJd6tzuA39HmEW/dI/1S2N7PAZiz8weA7//KzOTNNdcXaxgHL3R0KdAwBbqlqMV2NiiZ3F/CkF2+6a8NMTS8bBz76+3/Y5uH076OfPcWv0ayEK9J2dQZblam2fyl68mmKt9E2JY7nXZ386MEDloMI/AgN4+7XCNUV6jhhpoVebi09k+r5cTRSouudXU7QD4TlCjAwf6amYy23ZZwtZWSX/bvgegim0LreLYQ==";
const exported_modulus = "y649TdSXEmN6rGmrLoB6648jaaQoLarazFK97XOsvZNptpIyo/53Oa7ETobkAdYM1Ryz2jbhWxSFAd5MUf7iHmYsl93ULOfMxegt4hCdIf9FwcEL2pW+NGHTq3hsQcSDFw4re5v2O2WOH8ufWbETQE9LSfUSgbz3iiMH5ClCdU3rhbg3NovGshhAvIfMA2LCzI+ixSyOSWjNKuxt5W+Tx3QolfPePGixHEdmJ7ThVJ8KzVD4XtVlYxtKpGemqpgziXYfLt+Zj+SUbBbBfmOpe1xe+fIUwt9iKTHVLqlOsA+zTvWQ/lFr3PJ7aPIIStdeRcvEjlAmcyAkNPmStlwXXQ==";
const exported_product_code = "CbN0X8cICx8=";

const keygen = createKeyGen({
    algorithm: exported_algorithm,
    bits: exported_bits,
    private: exported_private,
    modulus: exported_modulus,
    productCode: exported_product_code,
});

const serial = keygen({
    userName,
    email,
    expDate: expDate ? new Date(expDate) : undefined,
    maxBuildDate: maxBuildDate ? new Date(maxBuildDate) : undefined,
    runningTimeLimit: runningTimeLimit ? parseInt(runningTimeLimit, 10) : undefined,
    hardwareId: hardwareId ? Buffer.from(hardwareId, "base64") : undefined,
    userData: userData ? Buffer.from(userData, "base64") : undefined,
});

console.log(serial);
