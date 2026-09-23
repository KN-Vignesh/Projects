export interface AiClient {
  complete(prompt: string): Promise<string>;
}

export function createAiClient(): AiClient {
  const apiKey = process.env.AI_API_KEY;
  const baseUrl = process.env.AI_BASE_URL ?? 'https://api.openai.com/v1';
  const model = process.env.AI_MODEL;
  if (!apiKey || !model) throw new Error('AI_API_KEY and AI_MODEL are required for diagnosis.');

  return {
    async complete(prompt: string) {
      const response = await fetch(`${baseUrl.replace(/\/$/, '')}/chat/completions`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, temperature: 0, messages: [{ role: 'user', content: prompt }] }),
      });
      if (!response.ok) throw new Error(`AI provider returned ${response.status}.`);
      const data = await response.json() as { choices?: Array<{ message?: { content?: string } }> };
      const content = data.choices?.[0]?.message?.content;
      if (!content) throw new Error('AI provider returned no diagnosis content.');
      return content;
    },
  };
}
