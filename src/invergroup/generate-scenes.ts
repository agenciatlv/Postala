import { mkdir, readFile, writeFile } from "node:fs/promises";
import RunwayML, { TaskFailedError } from "@runwayml/sdk";

// Image-to-video for scenes 2-6 of the Invergroup commercial (camera motion only, never text-to-video).
// gen4.5 costs 12 credits per second, so each 5s clip is 60 credits.
// Usage: npm run invergroup:scenes -- 2 3 4   (optional "--take=2" to name a re-generation)

const FIDELITY =
  "Keep the architecture, furniture and landscape exactly as in the image. No new buildings, no structural changes, no morphing. Photorealistic.";

const SCENES: Record<string, { image: string; prompt: string }> = {
  "2": {
    image: "02_torre_vertical_9x16.jpg",
    prompt:
      "Slow smooth camera tilt up from the couple walking on the sidewalk to the top of the tower. Trees sway gently, clouds drift slowly, warm sunset light. Static building.",
  },
  "3": {
    image: "03_lobby_9x16.jpg",
    prompt:
      "Slow dolly forward into the lobby. The two women talk with subtle natural gestures, soft light reflections on the glass walls. Calm, elegant.",
  },
  "4": {
    image: "04_cozinha_casal_9x16.jpg",
    prompt:
      "Very subtle slow push-in toward the couple at the kitchen island. They talk and smile naturally with minimal movement. Warm cozy morning atmosphere.",
  },
  "5": {
    image: "05_living_vista_9x16.jpg",
    prompt:
      "Slow push-in toward the balcony glass doors. The woman on the balcony moves slightly, soft sunlight, plants moving in a light breeze. Sea view stays the same.",
  },
  "6": {
    image: "06_quarto_vista_mar_9x16.jpg",
    prompt:
      "Slow gentle dolly toward the open balcony doors. The woman on the balcony turns a page, light breeze on the plants, golden light. Serene.",
  },
};

const SOURCE_DIR = "invergroup/pack";
const OUTPUT_DIR = "invergroup/runway";

const args = process.argv.slice(2);
const take = args.find((a) => a.startsWith("--take="))?.split("=")[1] ?? "1";
// A re-generation can pass its own, calmer motion prompt with --prompt="..."
const promptOverride = args.find((a) => a.startsWith("--prompt="))?.slice("--prompt=".length);
const ids = args.filter((a) => !a.startsWith("--"));
const selected = ids.length ? ids : Object.keys(SCENES);

const client = new RunwayML();
await mkdir(OUTPUT_DIR, { recursive: true });

async function generate(id: string) {
  const scene = SCENES[id];
  if (!scene) throw new Error(`Unknown scene ${id}`);

  const image = await readFile(`${SOURCE_DIR}/${scene.image}`);
  const promptText = `${promptOverride ?? scene.prompt} ${FIDELITY}`;

  try {
    const task = await client.imageToVideo
      .create({
        model: "gen4.5",
        promptImage: `data:image/jpeg;base64,${image.toString("base64")}`,
        promptText,
        ratio: "720:1280",
        duration: 5,
      })
      .waitForTaskOutput();

    // Output URLs expire, so keep a local copy.
    const file = `${OUTPUT_DIR}/cena0${id}_take${take}.mp4`;
    const response = await fetch(task.output[0]);
    await writeFile(file, Buffer.from(await response.arrayBuffer()));
    console.log(`Scene ${id}: task ${task.id} -> ${file}`);
    return { id, taskId: task.id, file, promptText };
  } catch (error) {
    if (error instanceof TaskFailedError) {
      console.error(`Scene ${id} failed:`, error.taskDetails);
      return { id, failed: error.taskDetails };
    }
    throw error;
  }
}

const results = await Promise.all(selected.map(generate));
await writeFile(`${OUTPUT_DIR}/log_take${take}_${Date.now()}.json`, JSON.stringify(results, null, 2));
