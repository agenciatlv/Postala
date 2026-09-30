import { mkdir, writeFile } from "node:fs/promises";
import RunwayML, { TaskFailedError } from "@runwayml/sdk";

// Billable: muse_image costs 1 credit per image (see docs.dev.runwayml.com/guides/pricing).
// Usage: npm run generate -- "your prompt here"
const promptText =
  process.argv.slice(2).join(" ") ||
  "A bright, minimal flat-lay of a coffee cup and a notebook on a pastel desk, social media post style";

const client = new RunwayML();

try {
  const task = await client.textToImage
    .create({
      model: "muse_image",
      promptText,
      ratio: "1600:1600",
    })
    .waitForTaskOutput();

  const url = task.output[0];
  console.log(`Task ${task.id} succeeded: ${url}`);

  // Output URLs expire, so keep a local copy.
  const response = await fetch(url);
  await mkdir("outputs", { recursive: true });
  const file = `outputs/${task.id}.png`;
  await writeFile(file, Buffer.from(await response.arrayBuffer()));
  console.log(`Saved to ${file}`);
} catch (error) {
  if (error instanceof TaskFailedError) {
    console.error("Generation failed:", error.taskDetails);
    process.exitCode = 1;
  } else {
    throw error;
  }
}
