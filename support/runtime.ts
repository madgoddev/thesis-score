

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";
import { type CalldataEncodable, type DecodedDeployData, ExecutionResult, type GenLayerChain, type GenLayerClient, type TransactionHash, TransactionHashVariant, TransactionStatus } from "genlayer-js/types";

export type Stage = "studionet" | "bradbury";
export type Operation = "deploy-finalized" | "submit-bradbury" | "smoke-studionet" | "smoke-bradbury";
export type Receipt = { status?: string | number; statusName?: string; status_name?: string; result?: string | number; resultName?: string; result_name?: string; txExecutionResult?: number; txExecutionResultName?: string; tx_execution_result?: number; tx_execution_result_name?: string; data?: { contract_address?: string }; to_address?: string; txDataDecoded?: DecodedDeployData; consensus_data?: { leader_receipt?: Array<{ mode?: string; execution_result?: string; genvm_result?: { raw_error?: unknown }; result?: { status?: string } }> } };
export type RuntimeConfig = { prefix: string; project: string; contractFile: string; sourceSha256: string };

export function address(value: unknown, label: string): string { if (typeof value !== "string" || !/^0x[0-9a-fA-F]{40}$/.test(value)) throw new Error(`${label} is not an address`); return value.toLowerCase(); }
export function txHash(value: unknown): TransactionHash { if (typeof value !== "string" || !/^0x[0-9a-fA-F]{64}$/.test(value)) throw new Error("SDK did not return a canonical transaction hash"); return value as TransactionHash; }
export function record(value: unknown, label: string): Record<string, unknown> { if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error(`${label} did not return an object`); return value as Record<string, unknown>; }
export function uint(value: unknown, label: string): number { if (typeof value === "number" && Number.isSafeInteger(value) && value >= 0) return value; if (typeof value === "bigint" && value >= 0n && value <= BigInt(Number.MAX_SAFE_INTEGER)) return Number(value); if (typeof value === "string" && /^(0|[1-9][0-9]*)$/.test(value) && BigInt(value) <= BigInt(Number.MAX_SAFE_INTEGER)) return Number(value); throw new Error(`${label} is not a safe unsigned integer`); }
export function stableJson(value: unknown): string { if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value); if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`; if (typeof value === "object") { const object = value as Record<string, unknown>; return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(",")}}`; } throw new Error("unsupported canonical JSON value"); }
export function alter(value: string): string { return `${value.slice(0, -1)}${value.endsWith("0") ? "1" : "0"}`; }
export function sha256Ascii(value: unknown): string { return `sha256:${createHash("sha256").update(stableJson(value), "ascii").digest("hex")}`; }

export function localSource(config: RuntimeConfig): { code: Uint8Array; hash: string } { const code = new Uint8Array(readFileSync(path.resolve(process.cwd(), config.contractFile))); const hash = createHash("sha256").update(code).digest("hex").toUpperCase(); if (hash !== config.sourceSha256) throw new Error(`Refusing unaudited source ${hash}`); return { code, hash }; }
export async function deployedSource(client: GenLayerClient<GenLayerChain>, target: `0x${string}`, expected: string): Promise<string> { const code = await client.getContractCode(target); if (typeof code !== "string" || code.length === 0) throw new Error("deployed source unavailable"); const hash = createHash("sha256").update(code, "utf8").digest("hex").toUpperCase(); if (hash !== expected) throw new Error(`deployed source mismatch ${hash}`); return hash; }
export async function readFinal(client: GenLayerClient<GenLayerChain>, target: `0x${string}`, functionName: string, args: CalldataEncodable[] = []): Promise<unknown> { return client.readContract({ address: target, functionName, args, transactionHashVariant: TransactionHashVariant.LATEST_FINAL }); }

function agreed(receipt: Receipt): boolean { const name = receipt.resultName ?? receipt.result_name; return name !== undefined ? name === "AGREE" || name === "MAJORITY_AGREE" : Number(receipt.result) === 1 || Number(receipt.result) === 6; }
function succeeded(receipt: Receipt): boolean { const name = receipt.txExecutionResultName ?? receipt.tx_execution_result_name; if (name !== undefined) return name === ExecutionResult.FINISHED_WITH_RETURN; const number = receipt.txExecutionResult ?? receipt.tx_execution_result; if (number !== undefined) return Number(number) === 1; const leader = receipt.consensus_data?.leader_receipt?.find((item) => item.mode === "leader"); return leader?.execution_result === "SUCCESS" && leader.genvm_result?.raw_error == null && leader.result?.status === "return"; }
function atStatus(receipt: Receipt, wanted: "FINALIZED" | "ACCEPTED"): boolean { const code = wanted === "FINALIZED" ? 7 : 5; const name = wanted === "FINALIZED" ? TransactionStatus.FINALIZED : TransactionStatus.ACCEPTED; return receipt.statusName === name || receipt.status_name === name || receipt.status === name || Number(receipt.status) === code; }
export async function waitReceipt(client: GenLayerClient<GenLayerChain>, hash: TransactionHash, wanted: "FINALIZED" | "ACCEPTED", retries: number, interval: number): Promise<Receipt> { const receipt = await client.waitForTransactionReceipt({ hash, status: wanted === "FINALIZED" ? TransactionStatus.FINALIZED : TransactionStatus.ACCEPTED, retries, interval }) as unknown as Receipt; if (!atStatus(receipt, wanted) || !agreed(receipt) || !succeeded(receipt)) throw new Error(`${wanted} receipt was not agreeing and successful`); return receipt; }
function receiptAddress(receipt: Receipt): `0x${string}` { const value = receipt.data?.contract_address ?? receipt.txDataDecoded?.contractAddress ?? receipt.to_address; address(value, "receipt contract address"); return value as `0x${string}`; }
function positive(name: string, fallback?: number): number { const value = Number(process.env[name]?.trim() || fallback); if (!Number.isSafeInteger(value) || value <= 0) throw new Error(`${name} must be positive`); return value; }
function stage(prefix: string): Stage { const value = process.env[`${prefix}_DEPLOY_STAGE`]?.trim().toLowerCase(); if (value !== "studionet" && value !== "bradbury") throw new Error(`${prefix}_DEPLOY_STAGE must be studionet or bradbury`); return value; }
function operation(prefix: string): Operation { const value = process.env[`${prefix}_OPERATION`]?.trim().toLowerCase(); if (value !== "deploy-finalized" && value !== "submit-bradbury" && value !== "smoke-studionet" && value !== "smoke-bradbury") throw new Error(`${prefix}_OPERATION is invalid`); return value; }
export function requiredContract(prefix: string): `0x${string}` { const value = process.env[`${prefix}_CONTRACT_ADDRESS`]?.trim(); address(value, `${prefix}_CONTRACT_ADDRESS`); return value as `0x${string}`; }

export async function runDeployment(client: GenLayerClient<GenLayerChain>, config: RuntimeConfig, verifyPolicy: (client: GenLayerClient<GenLayerChain>, target: `0x${string}`, policy: number, signer: string) => Promise<void>, smoke: (client: GenLayerClient<GenLayerChain>, stage: Stage, policy: number, retries: number, interval: number) => Promise<unknown>) {
  const selectedStage = stage(config.prefix); const selectedOperation = operation(config.prefix);
  if (selectedOperation === "deploy-finalized" && selectedStage !== "studionet") throw new Error("deploy-finalized is StudioNet-only");
  if (selectedOperation === "smoke-studionet" && selectedStage !== "studionet") throw new Error("smoke-studionet requires StudioNet");
  if ((selectedOperation === "submit-bradbury" || selectedOperation === "smoke-bradbury") && selectedStage !== "bradbury") throw new Error("Bradbury operation/stage mismatch");
  const expectedChain = selectedStage === "studionet" ? "61999" : "4221"; const expectedHost = selectedStage === "studionet" ? "studio.genlayer.com" : "rpc-bradbury.genlayer.com";
  const actualChain = String((client.chain as GenLayerChain).id); const rpc = (client.chain as GenLayerChain).rpcUrls.default.http[0] ?? ""; const actualHost = new URL(rpc).hostname.toLowerCase();
  if (actualChain !== expectedChain || actualHost !== expectedHost) throw new Error(`network guard failed ${actualChain}/${actualHost}`);
  const policy = positive(`${config.prefix}_POLICY_VERSION`); const retries = positive(`${config.prefix}_RECEIPT_RETRIES`, 1440); const interval = positive(`${config.prefix}_RECEIPT_INTERVAL_MS`, 5000);
  if (retries > 10000 || interval < 1000 || interval > 60000) throw new Error("receipt settings outside guarded limits");
  if (selectedOperation.startsWith("smoke-")) return smoke(client, selectedStage, policy, retries, interval);
  const source = localSource(config); const hash = txHash(await client.deployContract({ code: source.code, args: [policy] }));
  console.log(`Canonical GenLayer transaction: ${hash}`); console.log(`Source SHA-256: ${source.hash}`);
  if (selectedOperation === "submit-bradbury") { const receipt = await waitReceipt(client, hash, "ACCEPTED", retries, interval); const target = receiptAddress(receipt); console.log(`Provisional contract address: ${target}`); console.log("Finality: WAITING"); return { hash, target, sourceSha256: source.hash, finality: "WAITING" }; }
  const receipt = await waitReceipt(client, hash, "FINALIZED", retries, interval); const target = receiptAddress(receipt); const deployedSourceSha256 = await deployedSource(client, target, config.sourceSha256); await verifyPolicy(client, target, policy, client.account?.address ?? "");
  console.log(`${config.project} deployed at ${target}`); console.log("Finality: FINALIZED"); return { hash, target, sourceSha256: source.hash, deployedSourceSha256, policy, finality: "FINALIZED" };
}


