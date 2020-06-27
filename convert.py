
class Msg(object):

    def __init__(self):
        self.attachments = []

    def dbgPrint(self):
        print("date   :", self.date)
        print("from   :", self.sender)
        print("subject:", self.subject)
        print("body   :", repr(self.body[0:40]))

    def parseBody(self, body):
        body = body.decode('utf-8')
        lines = body.splitlines()
        newBody = []
        for line in lines:
            if line.startswith('On ') and line.endswith('wrote:'):
                break
            newBody.append(line)
        self.body = '\n'.join(newBody)

    def parseExtraPart(self, part):
        disp = part.get('Content-Disposition', '')
        if 'attachment' in disp:
            attachment = part.get_payload(decode=True)
            filename = extractFilename(disp)
            self.attachments.append((filename, attachment))
        return

    def saveAttachments(self):
        for filename, attachment in self.attachments:
            stream = open(filename, 'wb')
            stream.write(attachment)
            stream.close()
        return

def parseMbox():
    msgs = []
    import mailbox
    mbox = mailbox.mbox('DontMakeMeAngry.txt')
    for message in mbox:
        msg = Msg()
        msg.date = message['date']
        msg.sender = message['from']
        msg.subject = message['subject']
        if msg.subject.startswith('Fwd:'):
            continue
        msgs.append(msg)
        if message.is_multipart():
            print("   ", message.get_content_type())
            for part in message.get_payload():
                print("       ", part.get_content_type())
                if part.get_content_type() == 'text/plain':
                    content = part.get_payload(decode=True)
                    msg.parseBody(content)
                elif part.is_multipart():
                    for subpart in part.get_payload():
                        print("           ", subpart.get_content_type())
                        if subpart.get_content_type() == 'text/plain':
                            content = subpart.get_payload(decode=True)
                            msg.parseBody(content)
                else:
                    msg.parseExtraPart(part)
            print()
        else:
            print("   ", part.get_content_type())
            content = message.get_payload(decode=True)
            msg.parseBody(content)
            print()
    return msgs

def extractFilename(contentHeader):
    filename = 'unknown'
    quote = contentHeader.find('"')
    if quote >= 0:
        cquote = contentHeader.rfind('"')
        filename = contentHeader[quote+1:cquote]
    return filename

def main():
    msgs = parseMbox()
    for msg in msgs:
        msg.dbgPrint()
        msg.saveAttachments()
        print()
    return


main()
