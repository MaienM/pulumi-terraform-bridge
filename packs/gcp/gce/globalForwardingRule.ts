// *** WARNING: this file was generated by the Lumi Terraform Bridge (TFGEN) Tool. ***
// *** Do not edit by hand unless you're certain you know what you are doing! ***

import * as lumi from "@lumi/lumi";

export class GlobalForwardingRule extends lumi.NamedResource implements GlobalForwardingRuleArgs {
    public readonly description?: string;
    public readonly ipAddress?: string;
    public readonly ipProtocol?: string;
    public readonly portRange?: string;
    public readonly project?: string;
    public readonly region?: string;
    public readonly selfLink?: string;
    public readonly target: string;

    constructor(name: string, args: GlobalForwardingRuleArgs) {
        super(name);
        this.description = args.description;
        this.ipAddress = args.ipAddress;
        this.ipProtocol = args.ipProtocol;
        this.portRange = args.portRange;
        this.project = args.project;
        this.region = args.region;
        if (args.selfLink === undefined) {
            throw new Error("Property argument 'selfLink' is required, but was missing");
        }
        this.selfLink = args.selfLink;
        if (args.target === undefined) {
            throw new Error("Property argument 'target' is required, but was missing");
        }
        this.target = args.target;
    }
}

export interface GlobalForwardingRuleArgs {
    readonly description?: string;
    readonly ipAddress?: string;
    readonly ipProtocol?: string;
    readonly portRange?: string;
    readonly project?: string;
    readonly region?: string;
    readonly selfLink?: string;
    readonly target: string;
}
