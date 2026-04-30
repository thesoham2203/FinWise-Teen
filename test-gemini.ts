import { GoogleGenerativeAI } from '@google/generative-ai';
import * as dotenv from 'dotenv';
dotenv.config();

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

async function main() {
  try {
    const models = [
      'gemini-2.5-pro',
      'gemini-2.5-pro-latest',
      'gemini-2.5-flash',
      'gemini-2.5-flash-latest',
      'gemini-pro',
      'gemini-3-flash'
    ];

    for (const modelName of models) {
      try {
        const model = genAI.getGenerativeModel({ model: modelName });
        const result = await model.generateContent("Hello");
        console.log(`Success with: ${modelName} -> ${result.response.text().trim()}`);
      } catch (err: any) {
        console.log(`Error with ${modelName}: ${err.message}`);
      }
    }
  } catch (err: any) {
    console.error('Fatal error:', err.message);
  }
}

main();
