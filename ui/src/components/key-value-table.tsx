import React from "react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"

interface KeyValueTableProps {
    showHeader?: boolean
    data: { key: string; value: any }[]
    keyCellProps?: React.ComponentProps<"td">
    valueCellProps?: any
}

export function KeyValueTable({ data, showHeader, ...props }: KeyValueTableProps) {
    return (
        <div>
            <Table>
                {showHeader && (
                    <TableHeader>
                        <TableRow>
                            <TableHead>Key</TableHead>
                            <TableHead align='right'>Value</TableHead>
                        </TableRow>
                    </TableHeader>
                )}
                <TableBody>
                    {data.map((row) => (
                        <TableRow key={row.key}>
                            <TableCell scope='row' style={{ fontWeight: 'bold' }} {...props?.keyCellProps}>
                                {row.key}
                            </TableCell>
                            <TableCell {...props?.valueCellProps}>{row.value}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    )
}
