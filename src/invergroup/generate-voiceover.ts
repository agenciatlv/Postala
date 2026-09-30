import { mkdir, writeFile } from "node:fs/promises";
import RunwayML, { TaskFailedError } from "@runwayml/sdk";
import type { TextToSpeechCreateParams } from "@runwayml/sdk/resources/text-to-speech";

// Voiceover for the Invergroup commercial, one clip per line so each can start with its scene.
// eleven_v3 costs 1 credit per 50 characters (1 credit minimum per call).
// Usage: npm run invergroup:voice -- Martin Claudia

type PresetId = TextToSpeechCreateParams.ElevenV3["voice"]["presetId"];

export const LINES = [
  { scene: 1, text: "Hay lugares que no se miden en metros…" },
  { scene: 2, text: "…se miden en momentos." },
  { scene: 3, text: "Llegar a casa." },
  { scene: 4, text: "Las mañanas compartidas." },
  { scene: 5, text: "Las tardes frente al mar." },
  { scene: 6, text: "El descanso que merecés." },
  { scene: 7, text: "Invergroup. Donde empieza todo." },
];

const voices = process.argv.slice(2) as PresetId[];
if (!voices.length) throw new Error("Pass at least one preset voice id");

const client = new RunwayML();

for (const voice of voices) {
  const dir = `invergroup/voice/${voice}`;
  await mkdir(dir, { recursive: true });

  for (const line of LINES) {
    try {
      const task = await client.textToSpeech
        .create({
          model: "eleven_v3",
          promptText: line.text,
          voice: { type: "runway-preset", presetId: voice },
          stability: 0.6,
        })
        .waitForTaskOutput();

      const response = await fetch(task.output[0]);
      const file = `${dir}/linea${line.scene}.mp3`;
      await writeFile(file, Buffer.from(await response.arrayBuffer()));
      console.log(`${voice} line ${line.scene}: ${file}`);
    } catch (error) {
      if (error instanceof TaskFailedError) {
        console.error(`${voice} line ${line.scene} failed:`, error.taskDetails);
      } else {
        throw error;
      }
    }
  }
}
