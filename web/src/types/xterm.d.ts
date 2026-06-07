declare module "@xterm/xterm" {
  export interface IDisposable {
    dispose(): void;
  }

  export interface ITerminalOptions {
    allowProposedApi?: boolean;
    cursorBlink?: boolean;
    fontFamily?: string;
    fontSize?: number;
    lineHeight?: number;
    letterSpacing?: number;
    fontWeight?: string | number;
    fontWeightBold?: string | number;
    macOptionIsMeta?: boolean;
    macOptionClickForcesSelection?: boolean;
    rightClickSelectsWord?: boolean;
    scrollback?: number;
    theme?: Record<string, string>;
  }

  export interface IBufferNamespace {
    active: unknown;
  }

  export interface IParser {
    registerOscHandler(ident: number, callback: (data: string) => boolean): IDisposable;
  }

  export interface IUnicodeHandling {
    activeVersion: string;
  }

  export interface IResizeEvent {
    cols: number;
    rows: number;
  }

  export class Terminal {
    constructor(options?: ITerminalOptions);
    readonly parser: IParser;
    readonly buffer: IBufferNamespace;
    readonly unicode: IUnicodeHandling;
    readonly rows: number;
    readonly cols: number;
    readonly textarea?: HTMLTextAreaElement;
    options: ITerminalOptions;

    attachCustomKeyEventHandler(handler: (event: KeyboardEvent) => boolean): void;
    attachCustomWheelEventHandler(handler: (event: WheelEvent) => boolean): void;
    clearSelection(): void;
    dispose(): void;
    focus(): void;
    getSelection(): string;
    loadAddon(addon: { activate?(terminal: Terminal): void; dispose?(): void }): void;
    onData(callback: (data: string) => void): IDisposable;
    onResize(callback: (event: IResizeEvent) => void): IDisposable;
    open(parent: HTMLElement): void;
    paste(data: string): void;
    refresh(start: number, end: number): void;
    scrollLines(amount: number): void;
    write(data: string | Uint8Array): void;
  }
}
