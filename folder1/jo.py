from trytond.modules.company import CompanyReport
from trytond.modules.hr_ec.company import CompanyReportSignature
from trytond.pool import Pool
from trytond.transaction import Transaction

__all__ = [
    'SPIReportMixin', 'AccountPaymentSPITXT', 'WordWarranty',
    'AccountPaymentSPIODS', 'TreasuryAccountPayment', 'EntryNote',
    'PaymentRequest'
]


class SPIReportMixin(object):
    'SPI Report Mixin'

    @classmethod
    def get_context(cls, records, data):
        method = cls._get_lines
        if (records[0].lines[0].request.payment_type == 'party' or
                records[0].lines[0].request.type == 'account.invoice'):
            method = cls._get_grouped_party
        report_context = super(
            SPIReportMixin, cls).get_context(records, data)
        report_context['spi_lines'] = method
        report_context['spi_grouped_lines'] = cls._get_grouped_lines
        report_context['mount_value'] = cls.mount_value
        report_context['spi_party_lines'] = cls._get_party_lines
        return report_context

    @classmethod
    def _get_lines(cls, spi):
        data2 = {}
        for line in spi.lines:
            # 0 -> IDENTIFIER
            # 1 -> PARTY NAME
            # 2 -> ACCOUNT NUMBER
            # 3 -> AMOUNT
            # 4 -> PROVIDER ACCOUNT BANK BIC
            # 5 -> ACCOUNT_TYPE
            # 6 -> SPI NUMBER
            # 7 -> PAYMENT_DESCRIPTION
            # 8 -> BANK-BIC
            # 9 -> EGRESS-CONCEPT
            if not data2.get(line.id):
                data2.update({
                    line.id: [
                        int(str(line.request.number).split('-')[2]),
                        line.party.name,
                        line.bank_account.numbers[0].number,
                        0,
                        line.bank.bic,
                        line.bank_account.account_type,
                        spi.number,
                        str(line.description).replace(",", ""),
                        line.bank.bic,
                        line.egress_concept.code,
                        line.party.tax_identifier.code
                        ]})
            data2[line.id][3] += line.amount
        data = {}
        for payment_id, values in data2.items():
            bank_bic = "%08d" % (int(values[4]))
            account_type = None
            if values[5] == 'card':
                account_type = '5'
            if values[5] == 'savings':
                account_type = '2'
            if values[5] == 'current':
                account_type = '1'
            data.update({
                        payment_id: [
                            values[0],
                            values[1][0:28],
                            str(values[2]),
                            str(values[3]),
                            str(bank_bic),
                            account_type,
                            values[6],
                            values[7],
                            values[8],
                            values[9],
                            values[10]
                            ]
                        })
        print('lata datata es ', data)
        return data

    @classmethod
    def _get_grouped_lines(cls, spi):
        data2 = {}
        for line in spi.lines:
            # 0 -> IDENTIFIER
            # 1 -> PARTY NAME
            # 2 -> ACCOUNT NUMBER
            # 3 -> AMOUNT
            # 4 -> PROVIDER ACCOUNT BANK BI
            # 5 -> UNKNOW VALUE
            if not data2.get(line.bank_account.numbers[0].number):
                data2.update({
                    line.bank_account.numbers[0].number: [
                        line.party.tax_identifier.code,
                        line.party.name,
                        line.bank_account.numbers[0].number,
                        0,
                        line.bank.bic,
                        1,
                        ]})
            data2[line.bank_account.numbers[0].number][3] += line.amount
        data = {}
        for payment_id, values in data2.items():
            data.update({
                        payment_id: [
                            values[0],
                            values[1][0:28],
                            str(values[2]),
                            str(values[3]),
                            str(values[4]),
                            str(values[5])
                            ]
                        })
        return data

    @classmethod
    def _get_grouped_party(cls, spi):
        data2 = {}
        for line in spi.lines:
            # 0 -> IDENTIFIER
            # 1 -> PARTY NAME
            # 2 -> ACCOUNT NUMBER
            # 3 -> AMOUNT
            # 4 -> PROVIDER ACCOUNT BANK BIC
            # 5 -> ACCOUNT_TYPE
            # 6 -> SPI NUMBER
            # 7 -> PAYMENT_DESCRIPTION
            # 8 -> BANK-BIC
            # 9 -> EGRESS-CONCEPT
            description = line.description
            if line.request.type == 'account.invoice':
                description = spi.name
            if not data2.get(line.bank_account.numbers[0].number):
                data2.update({
                    line.bank_account.numbers[0].number: [
                        int(str(line.request.number).split('-')[2]),
                        line.party.name,
                        line.bank_account.numbers[0].number,
                        0,
                        line.bank.bic,
                        line.bank_account.account_type,
                        spi.number,
                        str(description).replace(",", ""),
                        line.bank.bic,
                        line.egress_concept.code,
                        line.party.tax_identifier.code,
                    ]})
            data2[line.bank_account.numbers[0].number][3] += line.amount
        data = {}
        for payment_id, values in data2.items():
            bank_bic = "%08d" % (int(values[4]))
            account_type = None
            if values[5] == 'card':
                account_type = '5'
            if values[5] == 'savings':
                account_type = '2'
            if values[5] == 'current':
                account_type = '1'
            data.update({
                payment_id: [
                    values[0],
                    values[1][0:28],
                    str(values[2]),
                    str(values[3]),
                    str(bank_bic),
                    account_type,
                    values[6],
                    values[7],
                    values[8],
                    values[9],
                    values[10]
                ]
            })
        return data

    @classmethod
    def _get_party_lines(cls, spi):
        data2 = {}
        for line in spi.lines:
            # 0 -> IDENTIFIER
            # 1 -> EMPLOYEE NAME
            # 3 -> AMOUNT
            # 4 -> TOTAL
            vals = []
            pool = Pool()
            PayslipRule = pool.get('payslip.line')

            if isinstance(line.origin, PayslipRule):
                vals = [
                    spi.company.rec_name,
                    'Pago Comisiones',
                    line.amount
                ]
            else:
                continue
                # vals = [
                #     line.origin.payslip_employee.party.tax_identifier.code,
                #     line.origin.payslip_employee.party.name,
                #     line.origin.amount
                # ]
            if line.party.name in data2:
                data2[line.party.name].append(vals)
            else:
                data2[line.party.name] = [vals]

        data = {}
        for payment_id, values in data2.items():
            values = sorted(values, key=lambda x: x[1])
            for value in values:
                vals = [
                        value[0],
                        value[1][0:28],
                        str(value[2])
                ]
                if payment_id in data:
                    data[payment_id].append(vals)
                else:
                    data[payment_id] = [vals]
        return data

    @classmethod
    def mount_value(cls, mount):
        val1 = "%.2f" % (mount)
        val2 = val1.replace(".", '')
        str_val_aux = str("%09d" % int(val2))
        str_val = str_val_aux[:-2] + '.' + str_val_aux[-2:]
        return str_val


class AccountPaymentSPITXT(SPIReportMixin, CompanyReport):
    __name__ = 'treasury.account.payment.spi.txt'


class AccountPaymentSPIODS(SPIReportMixin, CompanyReportSignature):
    __name__ = 'treasury.account.payment.spi.ods'


class AccountPaymentSPIzipTXT(SPIReportMixin, CompanyReport):
    __name__ = 'treasury.account.payment.spi.zip.txt'


class WordWarranty(SPIReportMixin, CompanyReport):
    'wordwarranty report'
    __name__ = 'wordwarranty.warranty.report'

    @classmethod
    def get_context(cls, records, data):
        report_context = super(WordWarranty, cls).get_context(
            records, data)
        return report_context


class TreasuryAccountPayment (CompanyReport):
    __name__ = 'treasury.account.payment.fodt'


class TreasuryAccountPaymentSpi (CompanyReportSignature):
    __name__ = 'treasury.account.payment.spi.fodt'


class TreasuryAccountPaymentSpiSummary (CompanyReportSignature):
    __name__ = 'treasury.account.payment.spi_summary.fodt'


class EntryNote(CompanyReportSignature):
    __name__ = 'treasury.entry.note'

    @classmethod
    def get_context(cls, records, data):
        report_context = super(EntryNote, cls).get_context(
            records, data)
        context = Transaction().context
        employee_id = context.get('employee')
        if employee_id:
            pool = Pool()
            Employee = pool.get('company.employee')
            employee, = Employee.browse([employee_id])
            report_context['user_print'] = employee.party.name
        else:
            report_context['user_print'] = f"Configurar usuario"
        return report_context


class PaymentRequest(CompanyReportSignature):
    __name__ = 'treasury.account.payment.request'
