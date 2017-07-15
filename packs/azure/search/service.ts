// *** WARNING: this file was generated by the Lumi Terraform Bridge (TFGEN) Tool. ***
// *** Do not edit by hand unless you're certain you know what you are doing! ***

import * as lumi from "@lumi/lumi";

export class Service extends lumi.NamedResource implements ServiceArgs {
    public readonly location: string;
    public readonly partitionCount?: number;
    public readonly replicaCount?: number;
    public readonly resourceGroupName: string;
    public readonly sku: string;
    public readonly tags?: {[key: string]: any};

    constructor(name: string, args: ServiceArgs) {
        super(name);
        if (args.location === undefined) {
            throw new Error("Property argument 'location' is required, but was missing");
        }
        this.location = args.location;
        this.partitionCount = args.partitionCount;
        this.replicaCount = args.replicaCount;
        if (args.resourceGroupName === undefined) {
            throw new Error("Property argument 'resourceGroupName' is required, but was missing");
        }
        this.resourceGroupName = args.resourceGroupName;
        if (args.sku === undefined) {
            throw new Error("Property argument 'sku' is required, but was missing");
        }
        this.sku = args.sku;
        this.tags = args.tags;
    }
}

export interface ServiceArgs {
    readonly location: string;
    readonly partitionCount?: number;
    readonly replicaCount?: number;
    readonly resourceGroupName: string;
    readonly sku: string;
    readonly tags?: {[key: string]: any};
}
